"""M-Pesa STK Push callback webhook — docs/api-design.md §11.

Kept separate from `views.py`: this endpoint's auth profile is nothing
like the rest of the API (no JWT, no `IsInstitutionMember` — an external,
unauthenticated-by-JWT caller) and its tenant resolution is structurally
different too (see below), so it doesn't belong on `InvoiceViewSet` or any
`TenantScopedModelViewSet`.

**Tenant resolution**: Safaricom calls back on the platform's fixed public
API host, not a per-institution subdomain, so `TenantMiddleware` can't
resolve a tenant from the `Host` header the normal way — this path is
added to its `EXEMPT_PATH_PREFIXES`. Rather than reach for the
`all_tenants_unsafe` escape hatch (which `docs/multitenancy.md` §3
explicitly reserves for `institutions`/platform-admin/management-command
call sites, not arbitrary Layer 1 apps), the callback URL Safaricom is
given (`services.initiate_mpesa_stk_push`) embeds both `institution_id`
and the specific `MpesaSTKPushRequest.id` directly — Daraja's STK Push API
takes a per-request `CallBackURL`, it isn't a fixed platform-wide endpoint.
This view resolves the institution from the URL, binds it, and then reads
`MpesaSTKPushRequest` via the ordinary structural `TenantManager` — no new
use of the unsafe escape hatch anywhere in this app.

**Verification, cheapest/safest-to-fail first**: (1) source-IP allowlist
(docs/api-design.md §13: "the source-IP allowlist is the actual control"
for webhooks — `throttle_classes = []` below, same reasoning); (2) the
institution/request actually exist; (3) `verification_token` matches via
`hmac.compare_digest` — Safaricom's callback carries no payload signature
of its own, so this embedded token is the closest equivalent actually
available.

**Always acks 200** with Safaricom's expected shape regardless of internal
outcome — a non-200 makes Safaricom retry indefinitely, and per §11 a
duplicate/no-op delivery must still ack cleanly, not error.
"""

import hmac
import logging
from datetime import datetime

from django.conf import settings
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.context import bind_institution
from apps.finance import services
from apps.finance.models import MpesaSTKPushRequest
from apps.institutions.models import Institution

logger = logging.getLogger(__name__)

_ACK = {"ResultCode": 0, "ResultDesc": "Accepted"}


def _get_client_ip(request) -> str:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def _parse_callback_metadata(stk_callback: dict) -> dict | None:
    metadata = stk_callback.get("CallbackMetadata")
    if not metadata:
        return None
    items = {item["Name"]: item.get("Value") for item in metadata.get("Item", [])}
    transaction_date = timezone.make_aware(
        datetime.strptime(str(items["TransactionDate"]), "%Y%m%d%H%M%S")
    )
    return {
        "amount": items["Amount"],
        "mpesa_receipt_number": str(items["MpesaReceiptNumber"]),
        "transaction_date": transaction_date,
        "phone_number": str(items.get("PhoneNumber", "")),
    }


class MpesaCallbackView(APIView):
    authentication_classes = []
    permission_classes = []
    throttle_classes = []

    # Excluded from the public API schema — this is an external
    # Safaricom-to-us webhook, not a documented client-facing endpoint.
    @extend_schema(exclude=True)
    def post(self, request, institution_id, stk_request_id, token):
        allowlist = settings.MPESA_CALLBACK_IP_ALLOWLIST
        if allowlist and _get_client_ip(request) not in allowlist:
            logger.warning("M-Pesa callback rejected: source IP not in allowlist")
            return Response(status=403)

        institution = Institution.objects.filter(id=institution_id).first()
        if institution is None:
            return Response(status=404)

        with bind_institution(institution):
            stk_request = MpesaSTKPushRequest.objects.filter(id=stk_request_id).first()
        if stk_request is None:
            return Response(status=404)

        if not hmac.compare_digest(stk_request.verification_token, str(token)):
            logger.warning("M-Pesa callback rejected: verification token mismatch")
            return Response(status=403)

        try:
            stk_callback = request.data["Body"]["stkCallback"]
            callback_metadata = _parse_callback_metadata(stk_callback)
            services.handle_mpesa_callback(
                institution=institution,
                stk_request=stk_request,
                result_code=stk_callback["ResultCode"],
                result_desc=stk_callback.get("ResultDesc", ""),
                callback_metadata=callback_metadata,
            )
        except (KeyError, TypeError, ValueError):
            # Malformed payload — logged, but still acked. A non-200
            # response here just makes Safaricom retry the same malformed
            # body forever; there's nothing a retry would fix.
            logger.exception(
                "M-Pesa callback payload could not be processed for request %s", stk_request_id
            )

        return Response(_ACK, status=200)

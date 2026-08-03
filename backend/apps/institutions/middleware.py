"""TenantMiddleware — resolves the request's tenant from the Host header
and binds it for the request's duration (docs/multitenancy.md §2).
"""

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponseNotFound
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

from apps.core.context import bind_institution
from apps.institutions.models import Institution
from apps.institutions.selectors import get_institution_by_domain

# Infra endpoints that must answer regardless of tenant resolution (an
# uptime monitor or Docker healthcheck has no institution context to send).
# The M-Pesa callback is exempt for a different reason: Safaricom calls
# back on the platform's fixed public API host, not a per-institution
# subdomain — the view itself resolves the institution from the URL
# (apps/finance/webhooks.py), not from Host-header tenant resolution.
EXEMPT_PATH_PREFIXES = ("/healthz/", "/api/v1/webhooks/mpesa/")


def _resolve_acting_institution(request):
    """Best-effort peek at a bearer token's `acting_as_admin` claim
    (docs/permissions.md §7's break-glass session), purely to decide
    whether to bind institution context on a platform host — this is
    never itself the authorization boundary. DRF's own `JWTAuthentication`
    still separately and fully re-validates the token before
    `request.user` is trusted; any failure here (missing header, bad
    signature, expired, not an acting-as token, revoked, institution
    gone) just means no institution gets bound, never a 500.
    """
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth_header.startswith("Bearer "):
        return None
    raw_token = auth_header.removeprefix("Bearer ")
    try:
        token = AccessToken(raw_token)
    except TokenError:
        return None
    if not token.get("acting_as_admin", False):
        return None
    jti = token.get("jti")
    if jti and cache.get(f"impersonation_revoked:{jti}"):
        return None
    institution_id = token.get("acting_institution_id")
    if not institution_id:
        return None
    return Institution.objects.filter(id=institution_id, is_active=True).first()


class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith(EXEMPT_PATH_PREFIXES):
            return self.get_response(request)

        # Always present for downstream permission classes/views to read,
        # regardless of which branch below actually runs.
        request.acting_as_admin = False

        host = request.get_host().split(":")[0]
        if host in settings.PLATFORM_HOSTS:
            # e.g. admin.educore.africa — platform-staff traffic. No
            # institution context, unless a valid break-glass act-as token
            # says otherwise (docs/permissions.md §7).
            acting_institution = _resolve_acting_institution(request)
            if acting_institution is not None:
                request.institution = acting_institution
                request.acting_as_admin = True
                with bind_institution(acting_institution):
                    return self.get_response(request)
            return self.get_response(request)

        institution = get_institution_by_domain(host)
        if institution is None:
            return HttpResponseNotFound()

        request.institution = institution
        with bind_institution(institution):
            return self.get_response(request)

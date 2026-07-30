import uuid
from decimal import Decimal

from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.core.context import bind_institution
from apps.finance.models import Invoice, MpesaSTKPushRequest, Payment
from apps.institutions.models import Institution

HOSTNAME = "st-mary.educore.africa"


def _stk_callback_body(result_code=0, checkout_request_id="ws_CO_1", include_metadata=True):
    stk_callback = {
        "MerchantRequestID": "29115-34620561-1",
        "CheckoutRequestID": checkout_request_id,
        "ResultCode": result_code,
        "ResultDesc": "The service request is processed successfully."
        if result_code == 0
        else "Request cancelled by user",
    }
    if include_metadata and result_code == 0:
        stk_callback["CallbackMetadata"] = {
            "Item": [
                {"Name": "Amount", "Value": 1000.0},
                {"Name": "MpesaReceiptNumber", "Value": "NLJ7RT61SV"},
                {"Name": "TransactionDate", "Value": 20260730143000},
                {"Name": "PhoneNumber", "Value": 254712345678},
            ]
        }
    return {"Body": {"stkCallback": stk_callback}}


class MpesaCallbackViewTests(APITestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        with bind_institution(self.institution):
            self.invoice = Invoice.objects.create(
                institution_id=self.institution.id,
                student_id=uuid.uuid4(),
                term_id=uuid.uuid4(),
                amount_due=Decimal("1000.00"),
            )
            self.stk_request = MpesaSTKPushRequest.objects.create(
                institution_id=self.institution.id,
                invoice=self.invoice,
                phone_number="254712345678",
                amount=Decimal("1000.00"),
                verification_token="correct-token",
                checkout_request_id="ws_CO_1",
            )
        self.url = reverse(
            "v1:mpesa-callback",
            kwargs={
                "institution_id": self.institution.id,
                "stk_request_id": self.stk_request.id,
                "token": "correct-token",
            },
        )

    def test_successful_callback_acks_200_and_creates_a_payment(self):
        response = self.client.post(
            self.url, _stk_callback_body(), format="json", HTTP_HOST=HOSTNAME
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["ResultCode"], 0)
        with bind_institution(self.institution):
            self.assertEqual(Payment.objects.filter(invoice=self.invoice).count(), 1)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, Invoice.Status.PAID)

    def test_wrong_token_is_rejected(self):
        url = reverse(
            "v1:mpesa-callback",
            kwargs={
                "institution_id": self.institution.id,
                "stk_request_id": self.stk_request.id,
                "token": "wrong-token",
            },
        )

        response = self.client.post(url, _stk_callback_body(), format="json", HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 403)
        with bind_institution(self.institution):
            self.assertEqual(Payment.objects.filter(invoice=self.invoice).count(), 0)

    def test_unknown_institution_is_a_404(self):
        url = reverse(
            "v1:mpesa-callback",
            kwargs={
                "institution_id": uuid.uuid4(),
                "stk_request_id": self.stk_request.id,
                "token": "correct-token",
            },
        )

        response = self.client.post(url, _stk_callback_body(), format="json", HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 404)

    def test_unknown_stk_request_is_a_404(self):
        url = reverse(
            "v1:mpesa-callback",
            kwargs={
                "institution_id": self.institution.id,
                "stk_request_id": uuid.uuid4(),
                "token": "correct-token",
            },
        )

        response = self.client.post(url, _stk_callback_body(), format="json", HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 404)

    def test_malformed_body_is_still_acked_200_with_no_payment(self):
        response = self.client.post(self.url, {"garbage": True}, format="json", HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 200)
        with bind_institution(self.institution):
            self.assertEqual(Payment.objects.filter(invoice=self.invoice).count(), 0)

    def test_duplicate_delivery_still_acks_200_with_exactly_one_payment(self):
        self.client.post(self.url, _stk_callback_body(), format="json", HTTP_HOST=HOSTNAME)

        response = self.client.post(
            self.url, _stk_callback_body(), format="json", HTTP_HOST=HOSTNAME
        )

        self.assertEqual(response.status_code, 200)
        with bind_institution(self.institution):
            self.assertEqual(Payment.objects.filter(invoice=self.invoice).count(), 1)

    def test_cancelled_result_code_creates_no_payment(self):
        response = self.client.post(
            self.url,
            _stk_callback_body(result_code=1032, include_metadata=False),
            format="json",
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 200)
        with bind_institution(self.institution):
            self.assertEqual(Payment.objects.filter(invoice=self.invoice).count(), 0)
        self.stk_request.refresh_from_db()
        self.assertEqual(self.stk_request.status, MpesaSTKPushRequest.Status.CANCELLED)

    @override_settings(MPESA_CALLBACK_IP_ALLOWLIST=["203.0.113.5"])
    def test_ip_not_in_allowlist_is_rejected(self):
        response = self.client.post(
            self.url,
            _stk_callback_body(),
            format="json",
            HTTP_HOST=HOSTNAME,
            REMOTE_ADDR="198.51.100.1",
        )

        self.assertEqual(response.status_code, 403)
        with bind_institution(self.institution):
            self.assertEqual(Payment.objects.filter(invoice=self.invoice).count(), 0)

    @override_settings(MPESA_CALLBACK_IP_ALLOWLIST=["198.51.100.1"])
    def test_ip_in_allowlist_is_accepted(self):
        response = self.client.post(
            self.url,
            _stk_callback_body(),
            format="json",
            HTTP_HOST=HOSTNAME,
            REMOTE_ADDR="198.51.100.1",
        )

        self.assertEqual(response.status_code, 200)
        with bind_institution(self.institution):
            self.assertEqual(Payment.objects.filter(invoice=self.invoice).count(), 1)

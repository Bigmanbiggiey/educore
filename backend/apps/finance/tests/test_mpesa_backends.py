from decimal import Decimal
from unittest.mock import Mock, patch

import requests
from django.test import TestCase, override_settings

from apps.finance.mpesa_backends import (
    DarajaGatewayBackend,
    FakeMpesaGatewayBackend,
    MpesaGatewayError,
)

_SETTINGS = {
    "MPESA_ENV": "sandbox",
    "MPESA_CONSUMER_KEY": "test-key",
    "MPESA_CONSUMER_SECRET": "test-secret",
    "MPESA_SHORTCODE": "174379",
    "MPESA_PASSKEY": "test-passkey",
}


class FakeMpesaGatewayBackendTests(TestCase):
    def test_returns_fake_ids_with_no_network(self):
        backend = FakeMpesaGatewayBackend()

        result = backend.initiate_stk_push(
            phone_number="254712345678",
            amount=Decimal("100"),
            account_reference="ref",
            transaction_desc="desc",
            callback_url="https://example.com/callback/",
        )

        self.assertIn("merchant_request_id", result)
        self.assertIn("checkout_request_id", result)


def _mock_response(status_code=200, json_data=None, text=""):
    response = Mock()
    response.status_code = status_code
    response.json.return_value = json_data or {}
    response.text = text
    return response


def _token_response():
    return _mock_response(json_data={"access_token": "tok-1", "expires_in": 3600})


@override_settings(**_SETTINGS)
class DarajaGatewayBackendTests(TestCase):
    @patch("apps.finance.mpesa_backends.requests.get")
    def test_get_access_token_caches_across_calls(self, mock_get):
        mock_get.return_value = _token_response()
        backend = DarajaGatewayBackend()

        first = backend._get_access_token()
        second = backend._get_access_token()

        self.assertEqual(first, "tok-1")
        self.assertEqual(second, "tok-1")
        mock_get.assert_called_once()

    @patch("apps.finance.mpesa_backends.requests.get")
    def test_get_access_token_raises_on_non_200(self, mock_get):
        mock_get.return_value = _mock_response(status_code=401, text="unauthorized")
        backend = DarajaGatewayBackend()

        with self.assertRaises(MpesaGatewayError):
            backend._get_access_token()

    @patch("apps.finance.mpesa_backends.requests.post")
    @patch("apps.finance.mpesa_backends.requests.get")
    def test_initiate_stk_push_success(self, mock_get, mock_post):
        mock_get.return_value = _token_response()
        mock_post.return_value = _mock_response(
            json_data={
                "ResponseCode": "0",
                "MerchantRequestID": "29115-34620561-1",
                "CheckoutRequestID": "ws_CO_1",
            }
        )
        backend = DarajaGatewayBackend()

        result = backend.initiate_stk_push(
            phone_number="254712345678",
            amount=Decimal("100"),
            account_reference="ref-123456789012",
            transaction_desc="Fee payment",
            callback_url="https://example.com/callback/",
        )

        self.assertEqual(result["merchant_request_id"], "29115-34620561-1")
        self.assertEqual(result["checkout_request_id"], "ws_CO_1")

        call_kwargs = mock_post.call_args.kwargs
        self.assertEqual(call_kwargs["headers"]["Authorization"], "Bearer tok-1")
        payload = call_kwargs["json"]
        self.assertEqual(payload["BusinessShortCode"], "174379")
        self.assertEqual(payload["Amount"], 100)
        self.assertEqual(payload["PartyA"], "254712345678")
        self.assertEqual(payload["CallBackURL"], "https://example.com/callback/")
        # Daraja caps AccountReference at 12 characters.
        self.assertLessEqual(len(payload["AccountReference"]), 12)

    @patch("apps.finance.mpesa_backends.requests.post")
    @patch("apps.finance.mpesa_backends.requests.get")
    def test_initiate_stk_push_raises_on_rejected_response(self, mock_get, mock_post):
        mock_get.return_value = _token_response()
        mock_post.return_value = _mock_response(
            json_data={"ResponseCode": "1", "ResponseDescription": "Invalid phone number"}
        )
        backend = DarajaGatewayBackend()

        with self.assertRaises(MpesaGatewayError):
            backend.initiate_stk_push(
                phone_number="not-a-phone",
                amount=Decimal("100"),
                account_reference="ref",
                transaction_desc="desc",
                callback_url="https://example.com/callback/",
            )

    @patch("apps.finance.mpesa_backends.requests.post")
    @patch("apps.finance.mpesa_backends.requests.get")
    def test_initiate_stk_push_raises_on_network_error(self, mock_get, mock_post):
        mock_get.return_value = _token_response()
        mock_post.side_effect = requests.ConnectionError("boom")
        backend = DarajaGatewayBackend()

        with self.assertRaises(MpesaGatewayError):
            backend.initiate_stk_push(
                phone_number="254712345678",
                amount=Decimal("100"),
                account_reference="ref",
                transaction_desc="desc",
                callback_url="https://example.com/callback/",
            )

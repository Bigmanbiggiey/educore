from unittest.mock import Mock, patch

import requests
from django.test import TestCase, override_settings

from apps.notifications_core.backends import (
    AfricasTalkingSMSBackend,
    ConsoleChannelBackend,
    NotificationDeliveryError,
    get_backend,
)

_SETTINGS = {
    "AFRICASTALKING_ENV": "sandbox",
    "AFRICASTALKING_USERNAME": "sandbox",
    "AFRICASTALKING_API_KEY": "test-key",
    "AFRICASTALKING_SENDER_ID": "",
}


class ConsoleChannelBackendTests(TestCase):
    def test_returns_a_provider_response_dict(self):
        response = ConsoleChannelBackend().send(
            recipient_address="+254700000000", subject="", body="Pay up"
        )
        self.assertEqual(response, {"backend": "console", "delivered_to": "+254700000000"})


def _mock_response(status_code=201, json_data=None, text=""):
    response = Mock()
    response.status_code = status_code
    response.json.return_value = json_data or {}
    response.text = text
    return response


@override_settings(**_SETTINGS)
class AfricasTalkingSMSBackendTests(TestCase):
    @patch("apps.notifications_core.backends.requests.post")
    def test_successful_send_returns_the_provider_payload(self, mock_post):
        payload = {
            "SMSMessageData": {
                "Message": "Sent to 1/1",
                "Recipients": [
                    {"number": "+254700000000", "status": "Success", "statusCode": 101}
                ],
            }
        }
        mock_post.return_value = _mock_response(json_data=payload)

        result = AfricasTalkingSMSBackend().send(
            recipient_address="+254700000000", subject="", body="Pay up"
        )

        self.assertEqual(result, payload)
        call_kwargs = mock_post.call_args.kwargs
        self.assertEqual(call_kwargs["headers"]["apiKey"], "test-key")
        self.assertEqual(call_kwargs["data"]["to"], "+254700000000")
        self.assertEqual(call_kwargs["data"]["message"], "Pay up")
        self.assertNotIn("from", call_kwargs["data"])

    @override_settings(AFRICASTALKING_SENDER_ID="SCHOOL")
    @patch("apps.notifications_core.backends.requests.post")
    def test_includes_sender_id_when_configured(self, mock_post):
        mock_post.return_value = _mock_response(
            json_data={
                "SMSMessageData": {
                    "Recipients": [{"number": "+254700000000", "status": "Success"}]
                }
            }
        )

        AfricasTalkingSMSBackend().send(
            recipient_address="+254700000000", subject="", body="Pay up"
        )

        self.assertEqual(mock_post.call_args.kwargs["data"]["from"], "SCHOOL")

    @patch("apps.notifications_core.backends.requests.post")
    def test_raises_when_the_recipient_status_is_not_success(self, mock_post):
        mock_post.return_value = _mock_response(
            json_data={
                "SMSMessageData": {
                    "Recipients": [
                        {"number": "+254700000000", "status": "InvalidPhoneNumber"}
                    ]
                }
            }
        )

        with self.assertRaises(NotificationDeliveryError):
            AfricasTalkingSMSBackend().send(
                recipient_address="+254700000000", subject="", body="Pay up"
            )

    @patch("apps.notifications_core.backends.requests.post")
    def test_raises_on_non_201_status(self, mock_post):
        mock_post.return_value = _mock_response(status_code=401, text="unauthorized")

        with self.assertRaises(NotificationDeliveryError):
            AfricasTalkingSMSBackend().send(
                recipient_address="+254700000000", subject="", body="Pay up"
            )

    @patch("apps.notifications_core.backends.requests.post")
    def test_raises_on_network_error(self, mock_post):
        mock_post.side_effect = requests.ConnectionError("boom")

        with self.assertRaises(NotificationDeliveryError):
            AfricasTalkingSMSBackend().send(
                recipient_address="+254700000000", subject="", body="Pay up"
            )


class GetBackendTests(TestCase):
    def test_resolves_the_configured_backend_for_a_channel(self):
        backend = get_backend("sms")
        self.assertIsInstance(backend, ConsoleChannelBackend)

    def test_unknown_channel_raises(self):
        with self.assertRaises(ValueError):
            get_backend("carrier_pigeon")

    @override_settings(NOTIFICATION_CHANNEL_BACKENDS={})
    def test_unconfigured_channel_raises(self):
        with self.assertRaises(ValueError):
            get_backend("sms")

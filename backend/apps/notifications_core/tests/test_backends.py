from django.test import TestCase, override_settings

from apps.notifications_core.backends import ConsoleChannelBackend, get_backend


class ConsoleChannelBackendTests(TestCase):
    def test_returns_a_provider_response_dict(self):
        response = ConsoleChannelBackend().send(
            recipient_address="+254700000000", subject="", body="Pay up"
        )
        self.assertEqual(response, {"backend": "console", "delivered_to": "+254700000000"})


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

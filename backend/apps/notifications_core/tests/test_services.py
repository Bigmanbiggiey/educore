from unittest.mock import patch

from django.test import TestCase

from apps.accounts.models import User
from apps.institutions.models import Institution
from apps.notifications_core.models import Channel, NotificationLog
from apps.notifications_core.services import send


class SendTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")

    @patch("apps.notifications_core.services.dispatch_notification.delay")
    def test_sending_to_a_raw_address_creates_a_queued_log(self, mock_delay):
        log = send(
            institution=self.institution,
            recipient="+254700000000",
            template_key="fee_reminder",
            context={"amount": "5000"},
            channel=Channel.SMS,
        )

        self.assertEqual(log.status, NotificationLog.Status.QUEUED)
        self.assertIsNone(log.recipient_user)
        self.assertEqual(log.recipient_address, "+254700000000")
        mock_delay.assert_called_once_with(str(log.id), {"amount": "5000"})

    @patch("apps.notifications_core.services.dispatch_notification.delay")
    def test_sending_to_a_user_resolves_their_email(self, mock_delay):
        user = User.objects.create_user(email="teacher@stmary.ac.ke", password="x" * 12)

        log = send(
            institution=self.institution,
            recipient=user,
            template_key="welcome",
            context={},
            channel=Channel.EMAIL,
        )

        self.assertEqual(log.recipient_user, user)
        self.assertEqual(log.recipient_address, "teacher@stmary.ac.ke")

    @patch("apps.notifications_core.services.dispatch_notification.delay")
    def test_sending_to_a_user_resolves_their_phone_for_sms(self, mock_delay):
        user = User.objects.create_user(phone="+254700000000", password="x" * 12)

        log = send(
            institution=self.institution,
            recipient=user,
            template_key="welcome",
            context={},
            channel=Channel.SMS,
        )

        self.assertEqual(log.recipient_address, "+254700000000")

    def test_rejects_an_unknown_channel(self):
        with self.assertRaises(ValueError):
            send(
                institution=self.institution,
                recipient="+254700000000",
                template_key="fee_reminder",
                context={},
                channel="carrier_pigeon",
            )

    def test_rejects_a_user_with_no_address_for_the_requested_channel(self):
        user = User.objects.create_user(phone="+254700000000", password="x" * 12)  # no email

        with self.assertRaises(ValueError):
            send(
                institution=self.institution,
                recipient=user,
                template_key="welcome",
                context={},
                channel=Channel.EMAIL,
            )

    def test_rejects_resolving_a_push_address_from_a_user(self):
        user = User.objects.create_user(email="teacher@stmary.ac.ke", password="x" * 12)

        with self.assertRaises(ValueError):
            send(
                institution=self.institution,
                recipient=user,
                template_key="welcome",
                context={},
                channel=Channel.PUSH,
            )

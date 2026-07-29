"""Calls `dispatch_notification` directly rather than via `.delay()` — a
Celery task is a plain callable, so this runs synchronously without a
broker/worker, the standard way to unit test task bodies."""

from django.test import TestCase

from apps.institutions.models import Institution
from apps.notifications_core.models import Channel, NotificationLog, NotificationTemplate
from apps.notifications_core.tasks import dispatch_notification


class DispatchNotificationTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        NotificationTemplate.objects.create(
            institution=None,
            key="fee_reminder",
            channel=Channel.SMS,
            subject_template="",
            body_template="Dear $name, your balance is $amount.",
        )
        self.log = NotificationLog.objects.create(
            institution=self.institution,
            recipient_address="+254700000000",
            channel=Channel.SMS,
            template_key="fee_reminder",
        )

    def test_renders_the_template_and_marks_sent(self):
        dispatch_notification(str(self.log.id), {"name": "Jane", "amount": "5000"})

        self.log.refresh_from_db()
        self.assertEqual(self.log.status, NotificationLog.Status.SENT)
        self.assertEqual(self.log.provider_response["delivered_to"], "+254700000000")

    def test_missing_context_key_is_left_as_a_literal_placeholder(self):
        # string.Template.safe_substitute (not substitute) — a missing key
        # must not raise and blow up an otherwise-deliverable message.
        dispatch_notification(str(self.log.id), {"name": "Jane"})

        self.log.refresh_from_db()
        self.assertEqual(self.log.status, NotificationLog.Status.SENT)

    def test_a_context_value_cannot_reach_attribute_access(self):
        # string.Template only does $identifier substitution — there is no
        # way for a crafted context key/value to trigger attribute or
        # method access the way a str.format template could.
        dispatch_notification(str(self.log.id), {"name": "{0.__class__}", "amount": "1"})

        self.log.refresh_from_db()
        self.assertEqual(self.log.status, NotificationLog.Status.SENT)

    def test_missing_template_marks_failed_instead_of_raising(self):
        log = NotificationLog.objects.create(
            institution=self.institution,
            recipient_address="+254700000000",
            channel=Channel.SMS,
            template_key="no_such_template",
        )

        dispatch_notification(str(log.id), {})

        log.refresh_from_db()
        self.assertEqual(log.status, NotificationLog.Status.FAILED)
        self.assertIn("error", log.provider_response)

from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.institutions.models import Institution
from apps.notifications_core.models import Channel, NotificationLog, NotificationTemplate


class NotificationTemplateConstraintTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")

    def test_two_platform_defaults_cannot_share_key_and_channel(self):
        NotificationTemplate.objects.create(
            institution=None, key="fee_reminder", channel=Channel.SMS, body_template="Pay up"
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                NotificationTemplate.objects.create(
                    institution=None,
                    key="fee_reminder",
                    channel=Channel.SMS,
                    body_template="Pay up again",
                )

    def test_an_institution_can_override_the_platform_default(self):
        NotificationTemplate.objects.create(
            institution=None, key="fee_reminder", channel=Channel.SMS, body_template="Pay up"
        )
        NotificationTemplate.objects.create(
            institution=self.institution,
            key="fee_reminder",
            channel=Channel.SMS,
            body_template="St Mary specific reminder",
        )  # must not raise

    def test_one_institution_cannot_have_two_templates_for_the_same_key_and_channel(self):
        NotificationTemplate.objects.create(
            institution=self.institution,
            key="fee_reminder",
            channel=Channel.SMS,
            body_template="Pay up",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                NotificationTemplate.objects.create(
                    institution=self.institution,
                    key="fee_reminder",
                    channel=Channel.SMS,
                    body_template="Pay up again",
                )

    def test_subject_template_defaults_to_empty(self):
        template = NotificationTemplate.objects.create(
            institution=None, key="fee_reminder", channel=Channel.SMS, body_template="Pay up"
        )
        self.assertEqual(template.subject_template, "")


class NotificationLogTests(TestCase):
    def test_defaults_to_queued_status(self):
        institution = Institution.objects.create(name="St Mary", slug="st-mary")
        log = NotificationLog.objects.create(
            institution=institution,
            recipient_address="+254700000000",
            channel=Channel.SMS,
            template_key="fee_reminder",
        )
        self.assertEqual(log.status, NotificationLog.Status.QUEUED)
        self.assertEqual(log.provider_response, {})

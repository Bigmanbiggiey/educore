from django.test import TestCase

from apps.institutions.models import Institution
from apps.notifications_core.models import Channel, NotificationTemplate
from apps.notifications_core.selectors import get_template


class GetTemplateTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")

    def test_falls_back_to_the_platform_default(self):
        default = NotificationTemplate.objects.create(
            institution=None, key="fee_reminder", channel=Channel.SMS, body_template="Pay up"
        )

        self.assertEqual(get_template(self.institution, "fee_reminder", Channel.SMS), default)

    def test_prefers_an_institution_specific_override(self):
        NotificationTemplate.objects.create(
            institution=None, key="fee_reminder", channel=Channel.SMS, body_template="Pay up"
        )
        override = NotificationTemplate.objects.create(
            institution=self.institution,
            key="fee_reminder",
            channel=Channel.SMS,
            body_template="St Mary specific",
        )

        self.assertEqual(get_template(self.institution, "fee_reminder", Channel.SMS), override)

    def test_raises_when_neither_exists(self):
        with self.assertRaises(NotificationTemplate.DoesNotExist):
            get_template(self.institution, "unknown_key", Channel.SMS)

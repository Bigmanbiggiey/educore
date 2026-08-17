"""Confirms the 0002 data migration's seeded institution-admin welcome
template actually exists post-migrate — mirrors
apps.permissions.tests.test_seed_roles's shape.
"""

from django.test import TestCase

from apps.notifications_core.models import NotificationTemplate


class SeedInstitutionAdminWelcomeTemplateTests(TestCase):
    def test_platform_default_template_exists(self):
        template = NotificationTemplate.objects.get(
            institution__isnull=True, key="institution_admin_welcome", channel="email"
        )
        self.assertIn("$reset_url", template.body_template)
        self.assertIn("$institution_name", template.subject_template)

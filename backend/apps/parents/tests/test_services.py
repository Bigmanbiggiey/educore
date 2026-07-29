import uuid

from django.test import TestCase

from apps.institutions.models import Institution
from apps.parents.services import create_parent_profile, update_notification_preferences


class ParentsServiceTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")


class CreateParentProfileTests(ParentsServiceTestCase):
    def test_creates_and_scopes_to_institution(self):
        profile = create_parent_profile(institution=self.institution, user_id=uuid.uuid4())
        self.assertEqual(profile.institution_id, self.institution.id)
        self.assertEqual(profile.preferred_language, "en")


class UpdateNotificationPreferencesTests(ParentsServiceTestCase):
    def test_updates_the_preferences(self):
        profile = create_parent_profile(institution=self.institution, user_id=uuid.uuid4())

        updated = update_notification_preferences(
            institution=self.institution, profile=profile, preferences={"sms": False, "email": True}
        )

        profile.refresh_from_db()
        self.assertEqual(profile.notification_preferences, {"sms": False, "email": True})
        self.assertEqual(updated.notification_preferences, {"sms": False, "email": True})

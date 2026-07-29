import uuid

from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.core.context import bind_institution
from apps.institutions.models import Institution
from apps.parents.models import ParentProfile


class ParentProfileConstraintTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.ctx = bind_institution(self.institution)
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)

    def test_unique_user_per_institution(self):
        user_id = uuid.uuid4()
        ParentProfile.objects.create(institution_id=self.institution.id, user_id=user_id)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ParentProfile.objects.create(institution_id=self.institution.id, user_id=user_id)

    def test_defaults(self):
        profile = ParentProfile.objects.create(
            institution_id=self.institution.id, user_id=uuid.uuid4()
        )
        self.assertEqual(profile.preferred_language, "en")
        self.assertEqual(profile.notification_preferences, {})

    def test_carries_timestamps(self):
        profile = ParentProfile.objects.create(
            institution_id=self.institution.id, user_id=uuid.uuid4()
        )
        self.assertIsNotNone(profile.created_at)
        self.assertIsNotNone(profile.updated_at)

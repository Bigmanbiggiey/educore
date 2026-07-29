import uuid

from django.test import TestCase

from apps.core.context import bind_institution
from apps.institutions.models import Institution
from apps.parents.models import ParentProfile
from apps.parents.selectors import get_children, get_parent_profile_by_user_id
from apps.students.models import GuardianRelationship, Student


class ParentsSelectorTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.ctx = bind_institution(self.institution)
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)


class GetParentProfileByUserIdTests(ParentsSelectorTestCase):
    def test_returns_the_matching_profile(self):
        user_id = uuid.uuid4()
        profile = ParentProfile.objects.create(institution_id=self.institution.id, user_id=user_id)

        self.assertEqual(get_parent_profile_by_user_id(user_id), profile)

    def test_returns_none_when_no_profile_exists(self):
        self.assertIsNone(get_parent_profile_by_user_id(uuid.uuid4()))


class GetChildrenTests(ParentsSelectorTestCase):
    def test_delegates_to_students_get_guardian_children(self):
        """The one sanctioned parents -> students import
        (docs/modules.md) — this proves the pass-through actually reaches
        real guardian-relationship data, not just that it doesn't error."""
        guardian_id = uuid.uuid4()
        student = Student.objects.create(
            institution_id=self.institution.id,
            admission_number="ADM-001",
            first_name="Jane",
            last_name="Doe",
        )
        GuardianRelationship.objects.create(
            institution_id=self.institution.id,
            student=student,
            guardian_user_id=guardian_id,
            relationship_type=GuardianRelationship.RelationshipType.PARENT,
        )

        self.assertEqual(list(get_children(guardian_id)), [student])

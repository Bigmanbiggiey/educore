import uuid

from django.test import TestCase

from apps.institutions.models import Institution
from apps.staff.models import StaffProfile
from apps.staff.services import create_staff_profile


class CreateStaffProfileTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")

    def test_creates_and_scopes_to_institution(self):
        staff = create_staff_profile(
            institution=self.institution,
            user_id=uuid.uuid4(),
            employee_number="EMP-001",
            first_name="Jane",
            last_name="Teacher",
            employment_type=StaffProfile.EmploymentType.FULL_TIME,
        )
        self.assertEqual(staff.institution_id, self.institution.id)

    def test_rejects_an_unknown_employment_type(self):
        with self.assertRaises(ValueError):
            create_staff_profile(
                institution=self.institution,
                user_id=uuid.uuid4(),
                employee_number="EMP-001",
                first_name="Jane",
                last_name="Teacher",
                employment_type="volunteer",
            )

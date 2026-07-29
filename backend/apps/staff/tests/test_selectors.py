import uuid

from django.test import TestCase

from apps.core.context import bind_institution
from apps.institutions.models import Institution
from apps.staff.models import StaffProfile
from apps.staff.selectors import get_staff_by_department, get_staff_by_user_id


class StaffSelectorTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.ctx = bind_institution(self.institution)
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)

    def _staff(self, **kwargs):
        defaults = {
            "institution_id": self.institution.id,
            "user_id": uuid.uuid4(),
            "employee_number": "EMP-001",
            "first_name": "Jane",
            "last_name": "Teacher",
            "employment_type": StaffProfile.EmploymentType.FULL_TIME,
        }
        defaults.update(kwargs)
        return StaffProfile.objects.create(**defaults)


class GetStaffByUserIdTests(StaffSelectorTestCase):
    def test_returns_the_matching_staff_profile(self):
        user_id = uuid.uuid4()
        staff = self._staff(user_id=user_id)

        self.assertEqual(get_staff_by_user_id(user_id), staff)

    def test_returns_none_when_no_staff_has_that_user_id(self):
        self.assertIsNone(get_staff_by_user_id(uuid.uuid4()))


class GetStaffByDepartmentTests(StaffSelectorTestCase):
    def test_returns_only_that_departments_staff(self):
        science_teacher = self._staff(employee_number="EMP-001", department="Science")
        self._staff(employee_number="EMP-002", department="Arts", user_id=uuid.uuid4())

        self.assertEqual(list(get_staff_by_department("Science")), [science_teacher])

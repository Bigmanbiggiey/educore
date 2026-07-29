import uuid

from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.core.context import bind_institution
from apps.institutions.models import Institution
from apps.staff.models import StaffProfile


class StaffTestCase(TestCase):
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


class StaffProfileConstraintTests(StaffTestCase):
    def test_unique_employee_number_per_institution(self):
        self._staff(employee_number="EMP-001")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._staff(employee_number="EMP-001", user_id=uuid.uuid4())

    def test_unique_user_per_institution(self):
        user_id = uuid.uuid4()
        self._staff(user_id=user_id, employee_number="EMP-001")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._staff(user_id=user_id, employee_number="EMP-002")

    def test_soft_delete_hides_but_does_not_remove(self):
        staff = self._staff()
        staff.delete()

        self.assertEqual(list(StaffProfile.objects.all()), [])
        self.assertTrue(StaffProfile.all_objects.filter(pk=staff.pk).exists())

    def test_carries_timestamps(self):
        staff = self._staff()
        self.assertIsNotNone(staff.created_at)
        self.assertIsNotNone(staff.updated_at)

    def test_department_defaults_to_empty(self):
        staff = self._staff()
        self.assertEqual(staff.department, "")

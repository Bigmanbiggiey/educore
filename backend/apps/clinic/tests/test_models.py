import uuid

from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.clinic.models import HealthRecord
from apps.core.context import bind_institution
from apps.institutions.models import Institution


class ClinicTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.ctx = bind_institution(self.institution)
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)


class HealthRecordConstraintTests(ClinicTestCase):
    def test_only_one_health_record_per_student(self):
        student_id = uuid.uuid4()
        HealthRecord.objects.create(institution_id=self.institution.id, student_id=student_id)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                HealthRecord.objects.create(
                    institution_id=self.institution.id, student_id=student_id
                )

    def test_different_students_may_each_have_a_record(self):
        HealthRecord.objects.create(institution_id=self.institution.id, student_id=uuid.uuid4())
        HealthRecord.objects.create(institution_id=self.institution.id, student_id=uuid.uuid4())
        # must not raise

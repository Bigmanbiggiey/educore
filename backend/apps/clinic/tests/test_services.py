import uuid

from django.test import TestCase

from apps.clinic.models import HealthRecord
from apps.clinic.services import add_medication, record_visit, set_health_record
from apps.core.context import bind_institution
from apps.institutions.models import Institution


class ClinicServiceTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")


class SetHealthRecordTests(ClinicServiceTestCase):
    def test_creates_a_new_record(self):
        student_id = uuid.uuid4()
        record = set_health_record(
            institution=self.institution, student_id=student_id, allergies="Peanuts"
        )
        self.assertEqual(record.allergies, "Peanuts")

    def test_re_setting_updates_in_place_rather_than_duplicating(self):
        student_id = uuid.uuid4()
        set_health_record(institution=self.institution, student_id=student_id, allergies="Peanuts")
        set_health_record(institution=self.institution, student_id=student_id, allergies="Dust")

        with bind_institution(self.institution):
            self.assertEqual(HealthRecord.objects.filter(student_id=student_id).count(), 1)
            self.assertEqual(
                HealthRecord.objects.get(student_id=student_id).allergies, "Dust"
            )


class RecordVisitAndMedicationTests(ClinicServiceTestCase):
    def test_record_visit_then_add_medication(self):
        visit = record_visit(
            institution=self.institution,
            student_id=uuid.uuid4(),
            visit_date="2026-02-01",
            treated_by_id=uuid.uuid4(),
            notes="Fever",
        )
        medication = add_medication(
            institution=self.institution, visit=visit, name="Paracetamol", dosage="500mg"
        )

        self.assertEqual(medication.visit_id, visit.id)
        self.assertEqual(medication.dosage, "500mg")

import uuid

from django.test import TestCase

from apps.clinic.selectors import get_health_record, get_medications, get_visits
from apps.clinic.services import add_medication, record_visit, set_health_record
from apps.institutions.models import Institution


class ClinicSelectorTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")


class GetHealthRecordTests(ClinicSelectorTestCase):
    def test_returns_none_when_no_record_exists(self):
        self.assertIsNone(get_health_record(self.institution, uuid.uuid4()))

    def test_returns_the_students_record(self):
        student_id = uuid.uuid4()
        set_health_record(institution=self.institution, student_id=student_id, allergies="Peanuts")

        record = get_health_record(self.institution, student_id)

        self.assertEqual(record.allergies, "Peanuts")


class GetVisitsAndMedicationsTests(ClinicSelectorTestCase):
    def test_get_visits_returns_only_the_students_visits(self):
        student_id = uuid.uuid4()
        visit = record_visit(
            institution=self.institution,
            student_id=student_id,
            visit_date="2026-02-01",
            treated_by_id=uuid.uuid4(),
        )
        record_visit(
            institution=self.institution,
            student_id=uuid.uuid4(),
            visit_date="2026-02-01",
            treated_by_id=uuid.uuid4(),
        )

        self.assertEqual(get_visits(self.institution, student_id), [visit])

    def test_get_medications_returns_only_the_visits_medications(self):
        visit = record_visit(
            institution=self.institution,
            student_id=uuid.uuid4(),
            visit_date="2026-02-01",
            treated_by_id=uuid.uuid4(),
        )
        other_visit = record_visit(
            institution=self.institution,
            student_id=uuid.uuid4(),
            visit_date="2026-02-01",
            treated_by_id=uuid.uuid4(),
        )
        medication = add_medication(institution=self.institution, visit=visit, name="Paracetamol")
        add_medication(institution=self.institution, visit=other_visit, name="Ibuprofen")

        self.assertEqual(get_medications(self.institution, visit.id), [medication])

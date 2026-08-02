from django.core.files.storage import default_storage
from django.test import TestCase

from apps.classes_streams.services import create_academic_year, create_class_grade, create_term
from apps.documents.models import Document
from apps.institutions.services import provision_institution
from apps.reports.services import generate_report_card, generate_report_cards_for_roster
from apps.students.services import create_student, enroll_student


class ReportsServiceTestCase(TestCase):
    def setUp(self):
        self.institution = provision_institution(
            name="St Mary", slug="st-mary-reports", curriculum_types=["844"]
        )
        academic_year = create_academic_year(
            institution=self.institution,
            year_label="2026",
            start_date="2026-01-01",
            end_date="2026-12-01",
        )
        self.term = create_term(
            institution=self.institution,
            academic_year=academic_year,
            name="Term 1",
            start_date="2026-01-01",
            end_date="2026-04-01",
        )
        self.class_grade = create_class_grade(
            institution=self.institution, term=self.term, name="Form 1", curriculum_type="844"
        )
        self.student = create_student(
            institution=self.institution,
            admission_number="A-001",
            first_name="Jane",
            last_name="Doe",
        )
        enroll_student(
            institution=self.institution,
            student=self.student,
            class_grade_id=self.class_grade.id,
            term_id=self.term.id,
        )


class GenerateReportCardTests(ReportsServiceTestCase):
    def test_generates_a_real_pdf_and_attaches_it_to_the_student(self):
        document = generate_report_card(
            institution=self.institution, student_id=self.student.id, term_id=self.term.id
        )

        self.assertTrue(document.minio_object_key.endswith(".pdf"))
        self.assertTrue(document.is_confidential)
        self.assertEqual(document.target, self.student)
        self.assertTrue(default_storage.exists(document.minio_object_key))
        pdf_bytes = default_storage.open(document.minio_object_key).read()
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_rejects_a_student_with_no_active_enrollment_for_the_term(self):
        unenrolled = create_student(
            institution=self.institution, admission_number="A-002", first_name="No", last_name="One"
        )

        with self.assertRaises(ValueError):
            generate_report_card(
                institution=self.institution, student_id=unenrolled.id, term_id=self.term.id
            )

    def test_rejects_an_unknown_student(self):
        with self.assertRaises(ValueError):
            generate_report_card(
                institution=self.institution,
                student_id="00000000-0000-4000-8000-000000000000",
                term_id=self.term.id,
            )


class GenerateReportCardsForRosterTests(ReportsServiceTestCase):
    def test_generates_one_document_per_student_in_the_roster(self):
        documents = generate_report_cards_for_roster(
            institution=self.institution, roster=[self.student], term_id=self.term.id
        )

        self.assertEqual(len(documents), 1)
        self.assertIsInstance(documents[0], Document)

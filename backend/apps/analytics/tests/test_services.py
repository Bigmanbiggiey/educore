import decimal
import uuid

from django.test import TestCase

from apps.analytics.services import compute_rollups
from apps.attendance.models import AttendanceRecord
from apps.attendance.services import mark_attendance
from apps.classes_streams.services import create_academic_year, create_class_grade, create_term
from apps.core.context import bind_institution
from apps.curriculum_844.services import (
    create_subject,
    recompute_mean_grade_snapshots,
    record_exam_result,
)
from apps.finance.services import create_fee_structure, generate_invoices_for_class, record_payment
from apps.institutions.models import Institution
from apps.students.services import create_student, enroll_student


class AnalyticsServiceTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")

    def _make_class(self, curriculum_type="844"):
        academic_year = create_academic_year(
            institution=self.institution,
            year_label="2026",
            start_date="2026-01-01",
            end_date="2026-12-01",
        )
        term = create_term(
            institution=self.institution,
            academic_year=academic_year,
            name="Term 1",
            start_date="2026-01-01",
            end_date="2026-04-01",
        )
        class_grade = create_class_grade(
            institution=self.institution, term=term, name="Form 1", curriculum_type=curriculum_type
        )
        return term, class_grade

    def _make_student(self, admission_number, class_grade, term):
        student = create_student(
            institution=self.institution,
            admission_number=admission_number,
            first_name="A",
            last_name="B",
        )
        enroll_student(
            institution=self.institution,
            student=student,
            class_grade_id=class_grade.id,
            term_id=term.id,
        )
        return student


class ComputeRollupsTests(AnalyticsServiceTestCase):
    def test_averages_attendance_and_fee_collection_across_the_roster(self):
        term, class_grade = self._make_class()
        student_a = self._make_student("A-001", class_grade, term)
        student_b = self._make_student("A-002", class_grade, term)

        # student_a: present both days (rate 1.0); student_b: present one
        # of two (rate 0.5) — class average 0.75.
        mark_attendance(
            institution=self.institution,
            term_id=term.id,
            date="2026-01-05",
            subject_type=AttendanceRecord.SubjectType.STUDENT,
            target_id=student_a.id,
            status=AttendanceRecord.Status.PRESENT,
        )
        mark_attendance(
            institution=self.institution,
            term_id=term.id,
            date="2026-01-06",
            subject_type=AttendanceRecord.SubjectType.STUDENT,
            target_id=student_a.id,
            status=AttendanceRecord.Status.PRESENT,
        )
        mark_attendance(
            institution=self.institution,
            term_id=term.id,
            date="2026-01-05",
            subject_type=AttendanceRecord.SubjectType.STUDENT,
            target_id=student_b.id,
            status=AttendanceRecord.Status.PRESENT,
        )
        mark_attendance(
            institution=self.institution,
            term_id=term.id,
            date="2026-01-06",
            subject_type=AttendanceRecord.SubjectType.STUDENT,
            target_id=student_b.id,
            status=AttendanceRecord.Status.ABSENT,
        )

        # Fee: 1000 due each; student_a pays 600, student_b pays in full —
        # 2000 due, 1600 collected, 80% collection rate.
        fee_structure = create_fee_structure(
            institution=self.institution,
            class_grade_id=class_grade.id,
            term_id=term.id,
            name="Term 1 Fees",
            line_items=[{"name": "Tuition", "amount": "1000.00"}],
        )
        invoices = generate_invoices_for_class(
            institution=self.institution,
            fee_structure=fee_structure,
            student_ids=[student_a.id, student_b.id],
        )
        invoice_a = next(i for i in invoices if i.student_id == student_a.id)
        invoice_b = next(i for i in invoices if i.student_id == student_b.id)
        record_payment(
            institution=self.institution,
            invoice=invoice_a,
            amount=decimal.Decimal("600.00"),
            method="cash",
            reference="R1",
            paid_at="2026-01-10T00:00:00+00:00",
            recorded_by_id=None,
        )
        record_payment(
            institution=self.institution,
            invoice=invoice_b,
            amount=decimal.Decimal("1000.00"),
            method="cash",
            reference="R2",
            paid_at="2026-01-10T00:00:00+00:00",
            recorded_by_id=None,
        )

        result = compute_rollups(
            institution=self.institution, class_grade=class_grade, term_id=term.id
        )

        self.assertEqual(result["attendance"].rate, decimal.Decimal("0.75"))
        self.assertEqual(result["fee_collection"].total_due, decimal.Decimal("2000.00"))
        self.assertEqual(result["fee_collection"].total_collected, decimal.Decimal("1600.00"))
        self.assertEqual(result["fee_collection"].collection_rate, decimal.Decimal("0.8"))

    def test_mean_grade_rollup_is_populated_only_for_844(self):
        term, class_grade = self._make_class(curriculum_type="844")
        student_a = self._make_student("A-001", class_grade, term)
        student_b = self._make_student("A-002", class_grade, term)

        subject = create_subject(
            institution=self.institution, subject_catalog_id=uuid.uuid4(), name="Math", code="MATH"
        )
        for student, score in ((student_a, "80"), (student_b, "60")):
            record_exam_result(
                institution=self.institution,
                student_id=student.id,
                term_id=term.id,
                details={
                    "subject_id": str(subject.id),
                    "exam_type": "end_term",
                    "score": score,
                    "max_score": "100",
                },
            )
        recompute_mean_grade_snapshots(
            institution=self.institution, term_id=term.id, class_grade_id=class_grade.id
        )

        result = compute_rollups(
            institution=self.institution, class_grade=class_grade, term_id=term.id
        )

        self.assertEqual(result["mean_grade"].mean_score, decimal.Decimal("70.00"))

    def test_mean_grade_rollup_is_none_for_a_non_844_curriculum(self):
        term, class_grade = self._make_class(curriculum_type="cbc")
        self._make_student("A-001", class_grade, term)

        result = compute_rollups(
            institution=self.institution, class_grade=class_grade, term_id=term.id
        )

        self.assertIsNone(result["mean_grade"].mean_score)

    def test_an_empty_roster_produces_all_none_rollups(self):
        term, class_grade = self._make_class()

        result = compute_rollups(
            institution=self.institution, class_grade=class_grade, term_id=term.id
        )

        self.assertIsNone(result["attendance"].rate)
        self.assertIsNone(result["fee_collection"].collection_rate)
        self.assertEqual(result["fee_collection"].total_due, decimal.Decimal("0"))
        self.assertIsNone(result["mean_grade"].mean_score)

    def test_recomputing_updates_in_place_rather_than_duplicating(self):
        term, class_grade = self._make_class()
        self._make_student("A-001", class_grade, term)

        compute_rollups(institution=self.institution, class_grade=class_grade, term_id=term.id)
        compute_rollups(institution=self.institution, class_grade=class_grade, term_id=term.id)

        from apps.analytics.models import AttendanceRateSnapshot

        with bind_institution(self.institution):
            self.assertEqual(
                AttendanceRateSnapshot.objects.filter(
                    class_grade_id=class_grade.id, term_id=term.id
                ).count(),
                1,
            )

import decimal
import uuid

from django.test import TestCase

from apps.analytics.models import AttendanceRateSnapshot, FeeCollectionSnapshot
from apps.analytics.selectors import (
    get_attendance_rollup,
    get_fee_collection_rollup,
    get_institution_summary,
    get_mean_grade_rollup,
)
from apps.classes_streams.services import create_academic_year, create_class_grade, create_term
from apps.core.context import bind_institution
from apps.institutions.models import Institution


class AnalyticsSelectorTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.class_grade_id = uuid.uuid4()
        self.term_id = uuid.uuid4()


class GetRollupTests(AnalyticsSelectorTestCase):
    def test_get_attendance_rollup_returns_none_when_not_yet_computed(self):
        self.assertIsNone(
            get_attendance_rollup(self.institution, self.class_grade_id, self.term_id)
        )

    def test_get_attendance_rollup_returns_the_snapshot(self):
        with bind_institution(self.institution):
            AttendanceRateSnapshot.objects.create(
                institution_id=self.institution.id,
                class_grade_id=self.class_grade_id,
                term_id=self.term_id,
                rate=decimal.Decimal("0.9"),
            )

        snapshot = get_attendance_rollup(self.institution, self.class_grade_id, self.term_id)

        self.assertEqual(snapshot.rate, decimal.Decimal("0.9"))

    def test_get_fee_collection_rollup_returns_the_snapshot(self):
        with bind_institution(self.institution):
            FeeCollectionSnapshot.objects.create(
                institution_id=self.institution.id,
                class_grade_id=self.class_grade_id,
                term_id=self.term_id,
                collection_rate=decimal.Decimal("0.5"),
            )

        snapshot = get_fee_collection_rollup(self.institution, self.class_grade_id, self.term_id)

        self.assertEqual(snapshot.collection_rate, decimal.Decimal("0.5"))

    def test_get_mean_grade_rollup_returns_none_when_not_yet_computed(self):
        self.assertIsNone(
            get_mean_grade_rollup(self.institution, self.class_grade_id, self.term_id)
        )


class GetInstitutionSummaryTests(AnalyticsSelectorTestCase):
    def _make_class(self, term):
        return create_class_grade(
            institution=self.institution, term=term, name="Form 1", curriculum_type="cbc"
        )

    def test_averages_rollups_across_every_class_in_the_term(self):
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
        class_a = self._make_class(term)
        class_b = create_class_grade(
            institution=self.institution, term=term, name="Form 2", curriculum_type="cbc"
        )
        with bind_institution(self.institution):
            AttendanceRateSnapshot.objects.create(
                institution_id=self.institution.id,
                class_grade_id=class_a.id,
                term_id=term.id,
                rate=decimal.Decimal("1.0"),
            )
            AttendanceRateSnapshot.objects.create(
                institution_id=self.institution.id,
                class_grade_id=class_b.id,
                term_id=term.id,
                rate=decimal.Decimal("0.5"),
            )

        summary = get_institution_summary(self.institution, term.id)

        self.assertEqual(summary["class_count"], 2)
        self.assertEqual(summary["average_attendance_rate"], decimal.Decimal("0.75"))
        self.assertIsNone(summary["average_collection_rate"])

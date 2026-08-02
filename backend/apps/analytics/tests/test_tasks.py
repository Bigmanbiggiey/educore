from django.test import TestCase

from apps.analytics.models import AttendanceRateSnapshot
from apps.analytics.tasks import nightly_analytics_rollup, recompute_class_rollups_task
from apps.classes_streams.services import (
    create_academic_year,
    create_class_grade,
    create_term,
    set_current_term,
)
from apps.core.context import bind_institution
from apps.institutions.models import Institution


class AnalyticsTaskTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
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
            institution=self.institution, term=self.term, name="Form 1", curriculum_type="cbc"
        )


class RecomputeClassRollupsTaskTests(AnalyticsTaskTestCase):
    def test_computes_a_rollup_row_for_the_given_class_and_term(self):
        recompute_class_rollups_task(
            str(self.institution.id), str(self.class_grade.id), str(self.term.id)
        )

        with bind_institution(self.institution):
            self.assertTrue(
                AttendanceRateSnapshot.objects.filter(
                    class_grade_id=self.class_grade.id, term_id=self.term.id
                ).exists()
            )


class NightlyAnalyticsRollupTests(AnalyticsTaskTestCase):
    def test_recomputes_every_class_in_the_current_term_for_every_institution(self):
        set_current_term(institution=self.institution, term=self.term)

        nightly_analytics_rollup()

        with bind_institution(self.institution):
            self.assertTrue(
                AttendanceRateSnapshot.objects.filter(
                    class_grade_id=self.class_grade.id, term_id=self.term.id
                ).exists()
            )

    def test_an_institution_with_no_current_term_is_skipped_without_raising(self):
        other = Institution.objects.create(name="No Term School", slug="no-term")

        nightly_analytics_rollup()  # must not raise for `other`

        with bind_institution(other):
            self.assertEqual(AttendanceRateSnapshot.objects.count(), 0)
        with bind_institution(self.institution):
            self.assertEqual(AttendanceRateSnapshot.objects.count(), 0)

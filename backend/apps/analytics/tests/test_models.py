import uuid

from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.analytics.models import AttendanceRateSnapshot, FeeCollectionSnapshot, MeanGradeRollup
from apps.core.context import bind_institution
from apps.institutions.models import Institution


class AnalyticsTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.ctx = bind_institution(self.institution)
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)
        self.class_grade_id = uuid.uuid4()
        self.term_id = uuid.uuid4()


class AttendanceRateSnapshotConstraintTests(AnalyticsTestCase):
    def test_unique_per_class_and_term(self):
        AttendanceRateSnapshot.objects.create(
            institution_id=self.institution.id,
            class_grade_id=self.class_grade_id,
            term_id=self.term_id,
            rate=0.9,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                AttendanceRateSnapshot.objects.create(
                    institution_id=self.institution.id,
                    class_grade_id=self.class_grade_id,
                    term_id=self.term_id,
                    rate=0.5,
                )


class FeeCollectionSnapshotConstraintTests(AnalyticsTestCase):
    def test_unique_per_class_and_term(self):
        FeeCollectionSnapshot.objects.create(
            institution_id=self.institution.id,
            class_grade_id=self.class_grade_id,
            term_id=self.term_id,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                FeeCollectionSnapshot.objects.create(
                    institution_id=self.institution.id,
                    class_grade_id=self.class_grade_id,
                    term_id=self.term_id,
                )


class MeanGradeRollupConstraintTests(AnalyticsTestCase):
    def test_unique_per_class_and_term(self):
        MeanGradeRollup.objects.create(
            institution_id=self.institution.id,
            class_grade_id=self.class_grade_id,
            term_id=self.term_id,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                MeanGradeRollup.objects.create(
                    institution_id=self.institution.id,
                    class_grade_id=self.class_grade_id,
                    term_id=self.term_id,
                )

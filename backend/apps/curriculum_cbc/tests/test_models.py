import uuid

from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.core.context import bind_institution
from apps.curriculum_cbc.models import (
    PCI,
    Competency,
    ContinuousAssessment,
    CoreValue,
    LearningArea,
)
from apps.institutions.models import Institution


class CurriculumCbcTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.ctx = bind_institution(self.institution)
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)

    def _learning_area(self, code="ENV"):
        return LearningArea.objects.create(
            institution_id=self.institution.id,
            subject_catalog_id=uuid.uuid4(),
            name="Environmental Activities",
            code=code,
        )

    def _competency(self, learning_area=None):
        return Competency.objects.create(
            institution_id=self.institution.id,
            learning_area=learning_area or self._learning_area(),
            strand="Weather",
            sub_strand="Sunny and rainy days",
        )


class LearningAreaConstraintTests(CurriculumCbcTestCase):
    def test_unique_code_per_institution(self):
        self._learning_area(code="ENV")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._learning_area(code="ENV")


class CoreValueConstraintTests(CurriculumCbcTestCase):
    def test_unique_name_per_institution(self):
        CoreValue.objects.create(institution_id=self.institution.id, name="Respect")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CoreValue.objects.create(institution_id=self.institution.id, name="Respect")


class PCIConstraintTests(CurriculumCbcTestCase):
    def test_unique_name_per_institution(self):
        PCI.objects.create(institution_id=self.institution.id, name="Environmental degradation")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PCI.objects.create(
                    institution_id=self.institution.id, name="Environmental degradation"
                )


class ContinuousAssessmentConstraintTests(CurriculumCbcTestCase):
    def test_unique_per_student_competency_term(self):
        competency = self._competency()
        student_id = uuid.uuid4()
        term_id = uuid.uuid4()
        ContinuousAssessment.objects.create(
            institution_id=self.institution.id,
            student_id=student_id,
            competency=competency,
            term_id=term_id,
            performance_level=ContinuousAssessment.PerformanceLevel.MEETING_EXPECTATION,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ContinuousAssessment.objects.create(
                    institution_id=self.institution.id,
                    student_id=student_id,
                    competency=competency,
                    term_id=term_id,
                    performance_level=ContinuousAssessment.PerformanceLevel.BELOW_EXPECTATION,
                )

    def test_same_student_different_competency_is_allowed(self):
        learning_area = self._learning_area()
        competency_one = self._competency(learning_area=learning_area)
        competency_two = Competency.objects.create(
            institution_id=self.institution.id,
            learning_area=learning_area,
            strand="Number Work",
        )
        student_id = uuid.uuid4()
        term_id = uuid.uuid4()
        ContinuousAssessment.objects.create(
            institution_id=self.institution.id,
            student_id=student_id,
            competency=competency_one,
            term_id=term_id,
            performance_level=ContinuousAssessment.PerformanceLevel.MEETING_EXPECTATION,
        )
        ContinuousAssessment.objects.create(
            institution_id=self.institution.id,
            student_id=student_id,
            competency=competency_two,
            term_id=term_id,
            performance_level=ContinuousAssessment.PerformanceLevel.MEETING_EXPECTATION,
        )  # must not raise

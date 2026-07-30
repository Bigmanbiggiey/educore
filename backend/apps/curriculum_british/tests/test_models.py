import uuid

from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.core.context import bind_institution
from apps.curriculum_british.models import Coursework, PredictedGrade, Subject, YearGroup
from apps.institutions.models import Institution


class CurriculumBritishTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.ctx = bind_institution(self.institution)
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)

    def _subject(self, code="MATH"):
        return Subject.objects.create(
            institution_id=self.institution.id,
            subject_catalog_id=uuid.uuid4(),
            name="Mathematics",
            code=code,
        )


class YearGroupConstraintTests(CurriculumBritishTestCase):
    def test_unique_class_grade_per_institution(self):
        class_grade_id = uuid.uuid4()
        YearGroup.objects.create(
            institution_id=self.institution.id,
            class_grade_id=class_grade_id,
            key_stage=YearGroup.KeyStage.KS3,
            name="Year 7",
            order=7,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                YearGroup.objects.create(
                    institution_id=self.institution.id,
                    class_grade_id=class_grade_id,
                    key_stage=YearGroup.KeyStage.KS3,
                    name="Year 7 (duplicate)",
                    order=7,
                )


class SubjectConstraintTests(CurriculumBritishTestCase):
    def test_unique_code_per_institution(self):
        self._subject(code="MATH")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._subject(code="MATH")


class CourseworkConstraintTests(CurriculumBritishTestCase):
    def test_unique_per_student_subject_term_component(self):
        subject = self._subject()
        student_id = uuid.uuid4()
        term_id = uuid.uuid4()
        Coursework.objects.create(
            institution_id=self.institution.id,
            student_id=student_id,
            subject=subject,
            term_id=term_id,
            component="Unit 1",
            score="60.00",
            max_score="100.00",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Coursework.objects.create(
                    institution_id=self.institution.id,
                    student_id=student_id,
                    subject=subject,
                    term_id=term_id,
                    component="Unit 1",
                    score="70.00",
                    max_score="100.00",
                )

    def test_a_different_component_is_allowed(self):
        subject = self._subject()
        student_id = uuid.uuid4()
        term_id = uuid.uuid4()
        Coursework.objects.create(
            institution_id=self.institution.id,
            student_id=student_id,
            subject=subject,
            term_id=term_id,
            component="Unit 1",
            score="60.00",
            max_score="100.00",
        )
        Coursework.objects.create(
            institution_id=self.institution.id,
            student_id=student_id,
            subject=subject,
            term_id=term_id,
            component="Unit 2",
            score="70.00",
            max_score="100.00",
        )  # must not raise

    def test_score_cannot_exceed_max_score(self):
        subject = self._subject()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Coursework.objects.create(
                    institution_id=self.institution.id,
                    student_id=uuid.uuid4(),
                    subject=subject,
                    term_id=uuid.uuid4(),
                    component="Unit 1",
                    score="101.00",
                    max_score="100.00",
                )


class PredictedGradeConstraintTests(CurriculumBritishTestCase):
    def test_unique_per_student_subject_academic_year(self):
        subject = self._subject()
        student_id = uuid.uuid4()
        academic_year_id = uuid.uuid4()
        PredictedGrade.objects.create(
            institution_id=self.institution.id,
            student_id=student_id,
            subject=subject,
            academic_year_id=academic_year_id,
            predicted_grade="A*",
            set_by=uuid.uuid4(),
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PredictedGrade.objects.create(
                    institution_id=self.institution.id,
                    student_id=student_id,
                    subject=subject,
                    academic_year_id=academic_year_id,
                    predicted_grade="B",
                    set_by=uuid.uuid4(),
                )

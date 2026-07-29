import uuid

from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.core.context import bind_institution
from apps.curriculum_844.models import ExamResult, MeanGradeSnapshot, Subject
from apps.institutions.models import Institution


class Curriculum844TestCase(TestCase):
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


class SubjectConstraintTests(Curriculum844TestCase):
    def test_unique_code_per_institution(self):
        self._subject(code="MATH")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._subject(code="MATH")


class ExamResultConstraintTests(Curriculum844TestCase):
    def test_unique_per_student_subject_term_exam_type(self):
        subject = self._subject()
        student_id = uuid.uuid4()
        term_id = uuid.uuid4()
        ExamResult.objects.create(
            institution_id=self.institution.id,
            student_id=student_id,
            subject=subject,
            term_id=term_id,
            exam_type=ExamResult.ExamType.CAT,
            score="60.00",
            max_score="100.00",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ExamResult.objects.create(
                    institution_id=self.institution.id,
                    student_id=student_id,
                    subject=subject,
                    term_id=term_id,
                    exam_type=ExamResult.ExamType.CAT,
                    score="70.00",
                    max_score="100.00",
                )

    def test_a_different_exam_type_is_allowed(self):
        subject = self._subject()
        student_id = uuid.uuid4()
        term_id = uuid.uuid4()
        ExamResult.objects.create(
            institution_id=self.institution.id,
            student_id=student_id,
            subject=subject,
            term_id=term_id,
            exam_type=ExamResult.ExamType.CAT,
            score="60.00",
            max_score="100.00",
        )
        ExamResult.objects.create(
            institution_id=self.institution.id,
            student_id=student_id,
            subject=subject,
            term_id=term_id,
            exam_type=ExamResult.ExamType.END_TERM,
            score="70.00",
            max_score="100.00",
        )  # must not raise

    def test_score_cannot_be_negative(self):
        subject = self._subject()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ExamResult.objects.create(
                    institution_id=self.institution.id,
                    student_id=uuid.uuid4(),
                    subject=subject,
                    term_id=uuid.uuid4(),
                    exam_type=ExamResult.ExamType.CAT,
                    score="-1.00",
                    max_score="100.00",
                )

    def test_score_cannot_exceed_max_score(self):
        subject = self._subject()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ExamResult.objects.create(
                    institution_id=self.institution.id,
                    student_id=uuid.uuid4(),
                    subject=subject,
                    term_id=uuid.uuid4(),
                    exam_type=ExamResult.ExamType.CAT,
                    score="101.00",
                    max_score="100.00",
                )

    def test_max_score_must_be_positive(self):
        subject = self._subject()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ExamResult.objects.create(
                    institution_id=self.institution.id,
                    student_id=uuid.uuid4(),
                    subject=subject,
                    term_id=uuid.uuid4(),
                    exam_type=ExamResult.ExamType.CAT,
                    score="0.00",
                    max_score="0.00",
                )


class MeanGradeSnapshotConstraintTests(Curriculum844TestCase):
    def test_unique_per_student_term(self):
        student_id = uuid.uuid4()
        term_id = uuid.uuid4()
        MeanGradeSnapshot.objects.create(
            institution_id=self.institution.id,
            student_id=student_id,
            term_id=term_id,
            mean_score="75.00",
            mean_grade="B+",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                MeanGradeSnapshot.objects.create(
                    institution_id=self.institution.id,
                    student_id=student_id,
                    term_id=term_id,
                    mean_score="80.00",
                    mean_grade="A-",
                )

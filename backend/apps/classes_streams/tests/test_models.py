import uuid

from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.classes_streams.models import (
    AcademicYear,
    ClassGrade,
    ClassTeacherAssignment,
    Stream,
    Term,
)
from apps.core.context import bind_institution
from apps.institutions.models import Institution, InstitutionCurriculum


class ClassesStreamsTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.ctx = bind_institution(self.institution)
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)

    def _academic_year(self, **kwargs):
        defaults = {
            "institution_id": self.institution.id,
            "year_label": "2026",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
        }
        defaults.update(kwargs)
        return AcademicYear.objects.create(**defaults)

    def _term(self, academic_year=None, **kwargs):
        defaults = {
            "institution_id": self.institution.id,
            "academic_year": academic_year or self._academic_year(),
            "name": "Term 1",
            "start_date": "2026-01-01",
            "end_date": "2026-04-01",
        }
        defaults.update(kwargs)
        return Term.objects.create(**defaults)

    def _class_grade(self, term=None, **kwargs):
        defaults = {
            "institution_id": self.institution.id,
            "term": term or self._term(),
            "name": "Grade 4",
            "curriculum_type": InstitutionCurriculum.CurriculumType.CBC,
        }
        defaults.update(kwargs)
        return ClassGrade.objects.create(**defaults)


class AcademicYearConstraintTests(ClassesStreamsTestCase):
    def test_unique_label_per_institution(self):
        self._academic_year(year_label="2026")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._academic_year(year_label="2026")

    def test_carries_timestamps(self):
        year = self._academic_year()
        self.assertIsNotNone(year.created_at)
        self.assertIsNotNone(year.updated_at)


class TermConstraintTests(ClassesStreamsTestCase):
    def test_unique_name_per_academic_year(self):
        academic_year = self._academic_year()
        self._term(academic_year=academic_year, name="Term 1")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._term(academic_year=academic_year, name="Term 1")

    def test_only_one_current_term_per_institution(self):
        self._term(name="Term 1", is_current=True)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._term(name="Term 2", is_current=True)

    def test_defaults_to_not_current(self):
        term = self._term()
        self.assertFalse(term.is_current)


class ClassGradeConstraintTests(ClassesStreamsTestCase):
    def test_unique_per_term(self):
        term = self._term()
        cbc = InstitutionCurriculum.CurriculumType.CBC
        self._class_grade(term=term, name="Grade 4", curriculum_type=cbc)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._class_grade(term=term, name="Grade 4", curriculum_type=cbc)

    def test_same_name_different_curriculum_is_allowed(self):
        term = self._term()
        self._class_grade(
            term=term, name="Y1", curriculum_type=InstitutionCurriculum.CurriculumType.CBC
        )
        self._class_grade(
            term=term, name="Y1", curriculum_type=InstitutionCurriculum.CurriculumType.BRITISH
        )  # must not raise


class StreamConstraintTests(ClassesStreamsTestCase):
    def test_unique_name_per_class_grade(self):
        class_grade = self._class_grade()
        Stream.objects.create(
            institution_id=self.institution.id, class_grade=class_grade, name="East"
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Stream.objects.create(
                    institution_id=self.institution.id, class_grade=class_grade, name="East"
                )


class ClassTeacherAssignmentConstraintTests(ClassesStreamsTestCase):
    def test_one_assignment_per_class_grade_when_no_stream(self):
        class_grade = self._class_grade()
        term = class_grade.term
        ClassTeacherAssignment.objects.create(
            institution_id=self.institution.id,
            class_grade=class_grade,
            term=term,
            staff_id=uuid.uuid4(),
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ClassTeacherAssignment.objects.create(
                    institution_id=self.institution.id,
                    class_grade=class_grade,
                    term=term,
                    staff_id=uuid.uuid4(),
                )

    def test_one_assignment_per_stream(self):
        class_grade = self._class_grade()
        term = class_grade.term
        stream = Stream.objects.create(
            institution_id=self.institution.id, class_grade=class_grade, name="East"
        )
        ClassTeacherAssignment.objects.create(
            institution_id=self.institution.id,
            class_grade=class_grade,
            stream=stream,
            term=term,
            staff_id=uuid.uuid4(),
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ClassTeacherAssignment.objects.create(
                    institution_id=self.institution.id,
                    class_grade=class_grade,
                    stream=stream,
                    term=term,
                    staff_id=uuid.uuid4(),
                )

    def test_class_level_and_stream_level_assignment_can_coexist(self):
        class_grade = self._class_grade()
        term = class_grade.term
        stream = Stream.objects.create(
            institution_id=self.institution.id, class_grade=class_grade, name="East"
        )
        ClassTeacherAssignment.objects.create(
            institution_id=self.institution.id,
            class_grade=class_grade,
            term=term,
            staff_id=uuid.uuid4(),
        )
        ClassTeacherAssignment.objects.create(
            institution_id=self.institution.id,
            class_grade=class_grade,
            stream=stream,
            term=term,
            staff_id=uuid.uuid4(),
        )  # must not raise

import uuid

from django.test import TestCase

from apps.classes_streams.models import ClassTeacherAssignment, Stream
from apps.classes_streams.services import (
    assign_class_teacher,
    create_academic_year,
    create_class_grade,
    create_stream,
    create_term,
    set_current_term,
)
from apps.core.context import bind_institution
from apps.institutions.models import Institution, InstitutionCurriculum


class ClassesStreamsServiceTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")

    def _academic_year(self):
        return create_academic_year(
            institution=self.institution,
            year_label="2026",
            start_date="2026-01-01",
            end_date="2026-12-31",
        )

    def _term(self, academic_year=None, **kwargs):
        # `academic_year or self._academic_year()` — short-circuited, so a
        # caller-supplied academic_year never triggers a redundant (and
        # colliding, since _academic_year hardcodes year_label="2026")
        # extra create.
        defaults = {
            "institution": self.institution,
            "academic_year": academic_year or self._academic_year(),
            "name": "Term 1",
            "start_date": "2026-01-01",
            "end_date": "2026-04-01",
        }
        defaults.update(kwargs)
        return create_term(**defaults)

    def _class_grade(self, term=None):
        return create_class_grade(
            institution=self.institution,
            term=term or self._term(),
            name="Grade 4",
            curriculum_type=InstitutionCurriculum.CurriculumType.CBC,
        )


class CreateAcademicYearTests(ClassesStreamsServiceTestCase):
    def test_creates_and_scopes_to_institution(self):
        year = self._academic_year()
        self.assertEqual(year.institution_id, self.institution.id)


class SetCurrentTermTests(ClassesStreamsServiceTestCase):
    def test_marks_the_term_current(self):
        term = self._term()
        set_current_term(institution=self.institution, term=term)

        term.refresh_from_db()
        self.assertTrue(term.is_current)

    def test_unsets_the_previous_current_term(self):
        academic_year = self._academic_year()
        first = self._term(academic_year=academic_year, name="Term 1")
        second = self._term(academic_year=academic_year, name="Term 2")

        set_current_term(institution=self.institution, term=first)
        set_current_term(institution=self.institution, term=second)

        first.refresh_from_db()
        second.refresh_from_db()
        self.assertFalse(first.is_current)
        self.assertTrue(second.is_current)

    def test_is_idempotent_for_the_same_term(self):
        term = self._term()
        set_current_term(institution=self.institution, term=term)
        set_current_term(institution=self.institution, term=term)  # must not raise

        term.refresh_from_db()
        self.assertTrue(term.is_current)


class CreateClassGradeTests(ClassesStreamsServiceTestCase):
    def test_rejects_an_unknown_curriculum_type(self):
        with self.assertRaises(ValueError):
            create_class_grade(
                institution=self.institution,
                term=self._term(),
                name="Grade 4",
                curriculum_type="klingon",
            )


class CreateStreamTests(ClassesStreamsServiceTestCase):
    def test_creates_and_scopes_to_institution(self):
        stream = create_stream(
            institution=self.institution, class_grade=self._class_grade(), name="East"
        )
        self.assertEqual(stream.institution_id, self.institution.id)
        self.assertIsInstance(stream, Stream)


class AssignClassTeacherTests(ClassesStreamsServiceTestCase):
    def test_creates_a_new_assignment(self):
        class_grade = self._class_grade()
        staff_id = uuid.uuid4()

        assignment = assign_class_teacher(
            institution=self.institution,
            class_grade=class_grade,
            term=class_grade.term,
            staff_id=staff_id,
        )

        self.assertEqual(assignment.staff_id, staff_id)
        with bind_institution(self.institution):
            self.assertEqual(ClassTeacherAssignment.objects.count(), 1)

    def test_reassigning_updates_rather_than_duplicates(self):
        class_grade = self._class_grade()
        term = class_grade.term
        first_staff = uuid.uuid4()
        second_staff = uuid.uuid4()

        assign_class_teacher(
            institution=self.institution, class_grade=class_grade, term=term, staff_id=first_staff
        )
        assign_class_teacher(
            institution=self.institution, class_grade=class_grade, term=term, staff_id=second_staff
        )

        with bind_institution(self.institution):
            self.assertEqual(ClassTeacherAssignment.objects.count(), 1)
            self.assertEqual(ClassTeacherAssignment.objects.first().staff_id, second_staff)

    def test_class_level_and_stream_level_assignments_are_independent(self):
        class_grade = self._class_grade()
        term = class_grade.term
        with bind_institution(self.institution):
            stream = Stream.objects.create(
                institution_id=self.institution.id, class_grade=class_grade, name="East"
            )

        assign_class_teacher(
            institution=self.institution, class_grade=class_grade, term=term, staff_id=uuid.uuid4()
        )
        assign_class_teacher(
            institution=self.institution,
            class_grade=class_grade,
            term=term,
            stream=stream,
            staff_id=uuid.uuid4(),
        )

        with bind_institution(self.institution):
            self.assertEqual(ClassTeacherAssignment.objects.count(), 2)

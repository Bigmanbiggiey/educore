import uuid

from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.core.context import bind_institution
from apps.curriculum_university.models import (
    CourseRegistration,
    Faculty,
    GPASnapshot,
    Graduation,
    Programme,
    School,
    Semester,
    Unit,
    UnitAssessment,
    UniversityDepartment,
)
from apps.institutions.models import Institution


class CurriculumUniversityTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.ctx = bind_institution(self.institution)
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)

    def _faculty(self, name="Science"):
        return Faculty.objects.create(institution_id=self.institution.id, name=name)

    def _school(self, faculty=None, name="Computing"):
        return School.objects.create(
            institution_id=self.institution.id, faculty=faculty or self._faculty(), name=name
        )

    def _department(self, school=None, name="Software Engineering"):
        return UniversityDepartment.objects.create(
            institution_id=self.institution.id, school=school or self._school(), name=name
        )

    def _programme(self, department=None, code="BSC-SE"):
        return Programme.objects.create(
            institution_id=self.institution.id,
            department=department or self._department(),
            programme_code=code,
            degree_level=Programme.DegreeLevel.BACHELORS,
            name="BSc Software Engineering",
        )

    def _unit(self, programme=None, code="CS101"):
        return Unit.objects.create(
            institution_id=self.institution.id,
            programme=programme or self._programme(),
            unit_code=code,
            name="Intro to Programming",
            credit_hours=3,
            semester_offered=1,
        )

    def _semester(self, term_id=None):
        return Semester.objects.create(
            institution_id=self.institution.id,
            term_id=term_id or uuid.uuid4(),
            number=1,
            name="Semester 1 2026",
        )


class FacultyConstraintTests(CurriculumUniversityTestCase):
    def test_unique_name_per_institution(self):
        self._faculty(name="Science")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._faculty(name="Science")


class SchoolConstraintTests(CurriculumUniversityTestCase):
    def test_unique_name_per_faculty(self):
        faculty = self._faculty()
        self._school(faculty=faculty, name="Computing")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._school(faculty=faculty, name="Computing")


class ProgrammeConstraintTests(CurriculumUniversityTestCase):
    def test_unique_programme_code_per_institution(self):
        self._programme(code="BSC-SE")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._programme(code="BSC-SE")


class UnitConstraintTests(CurriculumUniversityTestCase):
    def test_unique_unit_code_per_institution(self):
        self._unit(code="CS101")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._unit(code="CS101")


class SemesterConstraintTests(CurriculumUniversityTestCase):
    def test_unique_term_per_institution(self):
        term_id = uuid.uuid4()
        self._semester(term_id=term_id)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._semester(term_id=term_id)


class CourseRegistrationConstraintTests(CurriculumUniversityTestCase):
    def test_unique_per_student_unit_semester(self):
        unit = self._unit()
        semester = self._semester()
        student_id = uuid.uuid4()
        CourseRegistration.objects.create(
            institution_id=self.institution.id, student_id=student_id, unit=unit, semester=semester
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CourseRegistration.objects.create(
                    institution_id=self.institution.id,
                    student_id=student_id,
                    unit=unit,
                    semester=semester,
                )


class UnitAssessmentConstraintTests(CurriculumUniversityTestCase):
    def test_unique_per_student_unit_semester_type(self):
        unit = self._unit()
        semester = self._semester()
        student_id = uuid.uuid4()
        UnitAssessment.objects.create(
            institution_id=self.institution.id,
            student_id=student_id,
            unit=unit,
            semester=semester,
            assessment_type=UnitAssessment.AssessmentType.CAT,
            score="60.00",
            max_score="100.00",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                UnitAssessment.objects.create(
                    institution_id=self.institution.id,
                    student_id=student_id,
                    unit=unit,
                    semester=semester,
                    assessment_type=UnitAssessment.AssessmentType.CAT,
                    score="70.00",
                    max_score="100.00",
                )

    def test_score_cannot_exceed_max_score(self):
        unit = self._unit()
        semester = self._semester()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                UnitAssessment.objects.create(
                    institution_id=self.institution.id,
                    student_id=uuid.uuid4(),
                    unit=unit,
                    semester=semester,
                    assessment_type=UnitAssessment.AssessmentType.CAT,
                    score="101.00",
                    max_score="100.00",
                )


class GPASnapshotConstraintTests(CurriculumUniversityTestCase):
    def test_unique_per_student_semester(self):
        semester = self._semester()
        student_id = uuid.uuid4()
        GPASnapshot.objects.create(
            institution_id=self.institution.id,
            student_id=student_id,
            semester=semester,
            gpa="3.50",
            cgpa="3.40",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                GPASnapshot.objects.create(
                    institution_id=self.institution.id,
                    student_id=student_id,
                    semester=semester,
                    gpa="3.60",
                    cgpa="3.45",
                )


class GraduationConstraintTests(CurriculumUniversityTestCase):
    def test_unique_per_student_programme(self):
        programme = self._programme()
        student_id = uuid.uuid4()
        Graduation.objects.create(
            institution_id=self.institution.id,
            student_id=student_id,
            programme=programme,
            conferred_at="2026-06-01T00:00:00Z",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Graduation.objects.create(
                    institution_id=self.institution.id,
                    student_id=student_id,
                    programme=programme,
                    conferred_at="2026-06-01T00:00:00Z",
                )

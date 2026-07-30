import uuid
from decimal import Decimal

from django.test import TestCase

from apps.academics.models import GradingScale
from apps.core.context import bind_institution
from apps.curriculum_university.models import GPASnapshot, UnitAssessment
from apps.curriculum_university.services import (
    create_course_registration,
    create_department,
    create_faculty,
    create_programme,
    create_school,
    create_semester,
    create_unit,
    recompute_gpa_snapshots,
    record_unit_assessment,
)
from apps.institutions.models import Institution, InstitutionCurriculum

_UNIVERSITY = InstitutionCurriculum.CurriculumType.UNIVERSITY


class CurriculumUniversityServiceTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")

    def _faculty(self):
        return create_faculty(institution=self.institution, name="Science")

    def _school(self):
        return create_school(
            institution=self.institution, faculty=self._faculty(), name="Computing"
        )

    def _department(self):
        return create_department(
            institution=self.institution, school=self._school(), name="Software Engineering"
        )

    def _programme(self):
        return create_programme(
            institution=self.institution,
            department=self._department(),
            programme_code="BSC-SE",
            degree_level="bachelors",
            name="BSc Software Engineering",
        )

    def _unit(self, credit_hours=3):
        return create_unit(
            institution=self.institution,
            programme=self._programme(),
            unit_code="CS101",
            name="Intro to Programming",
            credit_hours=credit_hours,
            semester_offered=1,
        )

    def _semester(self, term_id=None):
        return create_semester(
            institution=self.institution,
            term_id=term_id or uuid.uuid4(),
            number=1,
            name="Semester 1",
        )


class RecordUnitAssessmentTests(CurriculumUniversityServiceTestCase):
    def test_creates_a_new_assessment(self):
        unit = self._unit()
        term_id = uuid.uuid4()
        self._semester(term_id=term_id)

        assessment = record_unit_assessment(
            institution=self.institution,
            student_id=uuid.uuid4(),
            term_id=term_id,
            details={
                "unit_id": str(unit.id),
                "assessment_type": "cat",
                "score": 65,
                "max_score": 100,
            },
        )

        self.assertEqual(assessment.score, Decimal("65"))

    def test_rejects_a_term_with_no_configured_semester(self):
        unit = self._unit()
        with self.assertRaises(ValueError):
            record_unit_assessment(
                institution=self.institution,
                student_id=uuid.uuid4(),
                term_id=uuid.uuid4(),
                details={
                    "unit_id": str(unit.id),
                    "assessment_type": "cat",
                    "score": 65,
                    "max_score": 100,
                },
            )

    def test_re_recording_the_same_assessment_type_updates_in_place(self):
        unit = self._unit()
        term_id = uuid.uuid4()
        self._semester(term_id=term_id)
        student_id = uuid.uuid4()
        details = {"unit_id": str(unit.id), "assessment_type": "cat", "score": 40, "max_score": 100}

        record_unit_assessment(
            institution=self.institution, student_id=student_id, term_id=term_id, details=details
        )
        details["score"] = 90
        record_unit_assessment(
            institution=self.institution, student_id=student_id, term_id=term_id, details=details
        )

        with bind_institution(self.institution):
            self.assertEqual(UnitAssessment.objects.count(), 1)
            self.assertEqual(UnitAssessment.objects.first().score, Decimal("90"))

    def test_rejects_details_missing_required_keys(self):
        with self.assertRaises(ValueError):
            record_unit_assessment(
                institution=self.institution,
                student_id=uuid.uuid4(),
                term_id=uuid.uuid4(),
                details={"assessment_type": "cat"},
            )

    def test_rejects_an_unknown_assessment_type(self):
        unit = self._unit()
        term_id = uuid.uuid4()
        self._semester(term_id=term_id)
        with self.assertRaises(ValueError):
            record_unit_assessment(
                institution=self.institution,
                student_id=uuid.uuid4(),
                term_id=term_id,
                details={
                    "unit_id": str(unit.id),
                    "assessment_type": "klingon",
                    "score": 1,
                    "max_score": 10,
                },
            )


class RecomputeGpaSnapshotsTests(CurriculumUniversityServiceTestCase):
    def test_creates_snapshots_for_registered_students(self):
        with bind_institution(self.institution):
            GradingScale.objects.create(
                institution_id=self.institution.id,
                curriculum_type=_UNIVERSITY,
                levels=[{"label": "A", "min": 0, "max": 100, "grade_point": 4.0}],
            )
        unit = self._unit()
        term_id = uuid.uuid4()
        semester = self._semester(term_id=term_id)
        student_id = uuid.uuid4()

        create_course_registration(
            institution=self.institution, student_id=student_id, unit=unit, semester=semester
        )
        record_unit_assessment(
            institution=self.institution,
            student_id=student_id,
            term_id=term_id,
            details={
                "unit_id": str(unit.id),
                "assessment_type": "final_exam",
                "score": 80,
                "max_score": 100,
            },
        )

        snapshots = recompute_gpa_snapshots(institution=self.institution, semester_id=semester.id)

        self.assertEqual(len(snapshots), 1)
        with bind_institution(self.institution):
            snapshot = GPASnapshot.objects.get(student_id=student_id)
        self.assertEqual(snapshot.gpa, Decimal("4.00"))

    def test_students_with_no_resolvable_grade_are_skipped(self):
        unit = self._unit()
        term_id = uuid.uuid4()
        semester = self._semester(term_id=term_id)
        student_id = uuid.uuid4()

        create_course_registration(
            institution=self.institution, student_id=student_id, unit=unit, semester=semester
        )
        # No GradingScale configured, so no grade_point resolves and this
        # student contributes no gradeable units — still no UnitAssessment
        # recorded either, so gpa stays None and no snapshot is created.

        snapshots = recompute_gpa_snapshots(institution=self.institution, semester_id=semester.id)

        self.assertEqual(snapshots, [])

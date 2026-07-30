import uuid
from decimal import Decimal

from django.test import TestCase

from apps.academics.models import GradingScale
from apps.core.context import bind_institution
from apps.curriculum_university.models import (
    Faculty,
    Programme,
    School,
    Semester,
    Unit,
    UnitAssessment,
    UniversityDepartment,
)
from apps.curriculum_university.selectors import compute_cgpa, compute_gpa, get_report_data
from apps.institutions.models import Institution, InstitutionCurriculum

_UNIVERSITY = InstitutionCurriculum.CurriculumType.UNIVERSITY


class CurriculumUniversitySelectorTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.ctx = bind_institution(self.institution)
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)

        faculty = Faculty.objects.create(institution_id=self.institution.id, name="Science")
        school = School.objects.create(
            institution_id=self.institution.id, faculty=faculty, name="Computing"
        )
        department = UniversityDepartment.objects.create(
            institution_id=self.institution.id, school=school, name="Software Engineering"
        )
        self.programme = Programme.objects.create(
            institution_id=self.institution.id,
            department=department,
            programme_code="BSC-SE",
            degree_level=Programme.DegreeLevel.BACHELORS,
            name="BSc Software Engineering",
        )
        self.semester = Semester.objects.create(
            institution_id=self.institution.id, term_id=uuid.uuid4(), number=1, name="Semester 1"
        )
        self.student_id = uuid.uuid4()

        GradingScale.objects.create(
            institution_id=self.institution.id,
            curriculum_type=_UNIVERSITY,
            levels=[
                {"label": "A", "min": 80, "max": 100, "grade_point": 4.0},
                {"label": "B", "min": 60, "max": 79.99, "grade_point": 3.0},
                {"label": "C", "min": 0, "max": 59.99, "grade_point": 2.0},
            ],
        )

    def _unit(self, code, credit_hours=3):
        return Unit.objects.create(
            institution_id=self.institution.id,
            programme=self.programme,
            unit_code=code,
            name=f"Unit {code}",
            credit_hours=credit_hours,
            semester_offered=1,
        )


class ComputeGpaTests(CurriculumUniversitySelectorTestCase):
    def test_returns_none_when_nothing_recorded(self):
        gpa = compute_gpa(self.institution, self.student_id, self.semester)
        self.assertIsNone(gpa)

    def test_weights_by_credit_hours(self):
        unit_a = self._unit("CS101", credit_hours=3)
        unit_b = self._unit("CS102", credit_hours=1)
        # unit_a: 90% -> grade_point 4.0, weight 3
        UnitAssessment.objects.create(
            institution_id=self.institution.id,
            student_id=self.student_id,
            unit=unit_a,
            semester=self.semester,
            assessment_type=UnitAssessment.AssessmentType.FINAL_EXAM,
            score="90.00",
            max_score="100.00",
        )
        # unit_b: 65% -> grade_point 3.0, weight 1
        UnitAssessment.objects.create(
            institution_id=self.institution.id,
            student_id=self.student_id,
            unit=unit_b,
            semester=self.semester,
            assessment_type=UnitAssessment.AssessmentType.FINAL_EXAM,
            score="65.00",
            max_score="100.00",
        )

        gpa = compute_gpa(self.institution, self.student_id, self.semester)

        # (4.0*3 + 3.0*1) / (3+1) = 15/4 = 3.75
        self.assertEqual(gpa, Decimal("3.75"))

    def test_averages_multiple_assessment_types_for_the_same_unit_first(self):
        unit = self._unit("CS101", credit_hours=3)
        UnitAssessment.objects.create(
            institution_id=self.institution.id,
            student_id=self.student_id,
            unit=unit,
            semester=self.semester,
            assessment_type=UnitAssessment.AssessmentType.CAT,
            score="100.00",
            max_score="100.00",
        )
        UnitAssessment.objects.create(
            institution_id=self.institution.id,
            student_id=self.student_id,
            unit=unit,
            semester=self.semester,
            assessment_type=UnitAssessment.AssessmentType.FINAL_EXAM,
            score="60.00",
            max_score="100.00",
        )

        gpa = compute_gpa(self.institution, self.student_id, self.semester)

        # mean = 80% -> grade_point 4.0
        self.assertEqual(gpa, Decimal("4.0"))


class ComputeCgpaTests(CurriculumUniversitySelectorTestCase):
    def test_spans_every_semester_the_student_has_ever_had(self):
        unit = self._unit("CS101", credit_hours=3)
        other_semester = Semester.objects.create(
            institution_id=self.institution.id, term_id=uuid.uuid4(), number=2, name="Semester 2"
        )
        UnitAssessment.objects.create(
            institution_id=self.institution.id,
            student_id=self.student_id,
            unit=unit,
            semester=self.semester,
            assessment_type=UnitAssessment.AssessmentType.FINAL_EXAM,
            score="90.00",
            max_score="100.00",
        )
        other_unit = self._unit("CS102", credit_hours=3)
        UnitAssessment.objects.create(
            institution_id=self.institution.id,
            student_id=self.student_id,
            unit=other_unit,
            semester=other_semester,
            assessment_type=UnitAssessment.AssessmentType.FINAL_EXAM,
            score="65.00",
            max_score="100.00",
        )

        cgpa = compute_cgpa(self.institution, self.student_id)

        self.assertEqual(cgpa, Decimal("3.5"))


class GetReportDataTests(CurriculumUniversitySelectorTestCase):
    def test_returns_empty_shape_when_no_semester_exists_for_the_term(self):
        data = get_report_data(self.institution, self.student_id, uuid.uuid4())
        self.assertEqual(data["unit_assessments"], [])
        self.assertIsNone(data["gpa"])

    def test_includes_unit_assessments_for_the_semester(self):
        unit = self._unit("CS101")
        UnitAssessment.objects.create(
            institution_id=self.institution.id,
            student_id=self.student_id,
            unit=unit,
            semester=self.semester,
            assessment_type=UnitAssessment.AssessmentType.CAT,
            score="70.00",
            max_score="100.00",
        )

        data = get_report_data(self.institution, self.student_id, self.semester.term_id)

        self.assertEqual(len(data["unit_assessments"]), 1)
        self.assertEqual(data["unit_assessments"][0]["unit"], "Unit CS101")

import uuid

from django.test import TestCase

from apps.academics.contracts import AssessmentEngine, ReportEngine
from apps.core.context import bind_institution
from apps.curriculum_university.engine import UniversityEngine
from apps.curriculum_university.services import (
    create_department,
    create_faculty,
    create_programme,
    create_school,
    create_semester,
    create_unit,
)
from apps.institutions.models import Institution


class UniversityEngineTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.engine = UniversityEngine()

    def _unit(self):
        faculty = create_faculty(institution=self.institution, name="Science")
        school = create_school(institution=self.institution, faculty=faculty, name="Computing")
        department = create_department(
            institution=self.institution, school=school, name="Software Engineering"
        )
        programme = create_programme(
            institution=self.institution,
            department=department,
            programme_code="BSC-SE",
            degree_level="bachelors",
            name="BSc Software Engineering",
        )
        return create_unit(
            institution=self.institution,
            programme=programme,
            unit_code="CS101",
            name="Intro to Programming",
            credit_hours=3,
            semester_offered=1,
        )


class UniversityEngineSatisfiesContractsTests(UniversityEngineTestCase):
    def test_is_an_assessment_engine_and_a_report_engine(self):
        self.assertIsInstance(self.engine, AssessmentEngine)
        self.assertIsInstance(self.engine, ReportEngine)


class UniversityEngineDelegationTests(UniversityEngineTestCase):
    def test_record_assessment_delegates_to_services(self):
        unit = self._unit()
        term_id = uuid.uuid4()
        create_semester(institution=self.institution, term_id=term_id, number=1, name="Semester 1")

        result = self.engine.record_assessment(
            institution=self.institution,
            student_id=uuid.uuid4(),
            term_id=term_id,
            details={
                "unit_id": str(unit.id),
                "assessment_type": "cat",
                "score": 55,
                "max_score": 100,
            },
        )

        self.assertEqual(result["assessment_type"], "cat")

    def test_compute_result_returns_none_with_no_semester_for_the_term(self):
        with bind_institution(self.institution):
            result = self.engine.compute_result(
                institution=self.institution, student_id=uuid.uuid4(), term_id=uuid.uuid4()
            )

        self.assertIsNone(result)

    def test_generate_report_data_delegates_to_selectors(self):
        student_id = uuid.uuid4()
        term_id = uuid.uuid4()

        with bind_institution(self.institution):
            data = self.engine.generate_report_data(
                institution=self.institution, student_id=student_id, term_id=term_id
            )

        self.assertEqual(data["unit_assessments"], [])

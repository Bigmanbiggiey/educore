import uuid

from django.test import TestCase

from apps.academics.contracts import AssessmentEngine, ReportEngine
from apps.core.context import bind_institution
from apps.curriculum_tvet.engine import TVETEngine
from apps.curriculum_tvet.services import create_competency_unit, create_course, create_department
from apps.institutions.models import Institution


class TVETEngineTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.engine = TVETEngine()

    def _competency_unit(self):
        department = create_department(institution=self.institution, name="Engineering")
        course = create_course(
            institution=self.institution,
            department=department,
            course_code="ENG101",
            name="Automotive Engineering",
        )
        return create_competency_unit(
            institution=self.institution,
            course=course,
            unit_code="CU101",
            name="Engine Repair",
            credit_hours=10,
        )


class TVETEngineSatisfiesContractsTests(TVETEngineTestCase):
    def test_is_an_assessment_engine_and_a_report_engine(self):
        self.assertIsInstance(self.engine, AssessmentEngine)
        self.assertIsInstance(self.engine, ReportEngine)


class TVETEngineDelegationTests(TVETEngineTestCase):
    def test_record_assessment_delegates_to_services(self):
        competency_unit = self._competency_unit()
        student_id = uuid.uuid4()
        term_id = uuid.uuid4()

        result = self.engine.record_assessment(
            institution=self.institution,
            student_id=student_id,
            term_id=term_id,
            details={
                "competency_unit_id": str(competency_unit.id),
                "assessment_type": "workshop",
                "score": 55,
                "max_score": 100,
                "assessor_id": str(uuid.uuid4()),
            },
        )

        self.assertEqual(result["assessment_type"], "workshop")

    def test_compute_result_returns_none_when_nothing_recorded(self):
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

        self.assertEqual(data["practical_assessments"], [])

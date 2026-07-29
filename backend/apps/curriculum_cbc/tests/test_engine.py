import uuid

from django.test import TestCase

from apps.academics.contracts import AssessmentEngine, ReportEngine
from apps.core.context import bind_institution
from apps.curriculum_cbc.engine import CBCEngine
from apps.curriculum_cbc.services import create_competency, create_learning_area
from apps.institutions.models import Institution


class CBCEngineTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.engine = CBCEngine()

    def _competency(self):
        learning_area = create_learning_area(
            institution=self.institution,
            subject_catalog_id=uuid.uuid4(),
            name="Environmental Activities",
            code="ENV",
        )
        return create_competency(
            institution=self.institution, learning_area=learning_area, strand="Weather"
        )


class CBCEngineSatisfiesContractsTests(CBCEngineTestCase):
    def test_is_an_assessment_engine_and_a_report_engine(self):
        self.assertIsInstance(self.engine, AssessmentEngine)
        self.assertIsInstance(self.engine, ReportEngine)


class CBCEngineDelegationTests(CBCEngineTestCase):
    def test_record_assessment_delegates_to_services(self):
        competency = self._competency()
        student_id = uuid.uuid4()
        term_id = uuid.uuid4()

        result = self.engine.record_assessment(
            institution=self.institution,
            student_id=student_id,
            term_id=term_id,
            details={
                "competency_id": str(competency.id),
                "performance_level": "meeting_expectation",
            },
        )

        self.assertEqual(result["performance_level"], "meeting_expectation")

    def test_generate_report_data_delegates_to_selectors(self):
        student_id = uuid.uuid4()
        term_id = uuid.uuid4()

        with bind_institution(self.institution):
            data = self.engine.generate_report_data(
                institution=self.institution, student_id=student_id, term_id=term_id
            )

        self.assertEqual(data["learning_areas"], [])

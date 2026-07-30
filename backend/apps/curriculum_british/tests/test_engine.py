import uuid

from django.test import TestCase

from apps.academics.contracts import AssessmentEngine, ReportEngine
from apps.core.context import bind_institution
from apps.curriculum_british.engine import BritishEngine
from apps.curriculum_british.services import create_subject
from apps.institutions.models import Institution


class BritishEngineTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.engine = BritishEngine()

    def _subject(self):
        return create_subject(
            institution=self.institution,
            subject_catalog_id=uuid.uuid4(),
            name="Mathematics",
            code="MATH",
        )


class BritishEngineSatisfiesContractsTests(BritishEngineTestCase):
    def test_is_an_assessment_engine_and_a_report_engine(self):
        self.assertIsInstance(self.engine, AssessmentEngine)
        self.assertIsInstance(self.engine, ReportEngine)


class BritishEngineDelegationTests(BritishEngineTestCase):
    def test_record_assessment_delegates_to_services(self):
        subject = self._subject()
        student_id = uuid.uuid4()
        term_id = uuid.uuid4()

        result = self.engine.record_assessment(
            institution=self.institution,
            student_id=student_id,
            term_id=term_id,
            details={
                "subject_id": str(subject.id),
                "component": "Unit 1",
                "score": 55,
                "max_score": 100,
            },
        )

        self.assertEqual(result["component"], "Unit 1")

    def test_compute_result_returns_none_when_nothing_recorded(self):
        student_id = uuid.uuid4()
        term_id = uuid.uuid4()

        with bind_institution(self.institution):
            result = self.engine.compute_result(
                institution=self.institution, student_id=student_id, term_id=term_id
            )

        self.assertIsNone(result)

    def test_generate_report_data_delegates_to_selectors(self):
        student_id = uuid.uuid4()
        term_id = uuid.uuid4()

        with bind_institution(self.institution):
            data = self.engine.generate_report_data(
                institution=self.institution, student_id=student_id, term_id=term_id
            )

        self.assertEqual(data["courseworks"], [])

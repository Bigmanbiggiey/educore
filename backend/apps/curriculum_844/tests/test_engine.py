import uuid
from decimal import Decimal

from django.test import TestCase

from apps.academics.contracts import AssessmentEngine, ReportEngine
from apps.core.context import bind_institution
from apps.curriculum_844.engine import EightFourFourEngine
from apps.curriculum_844.services import create_subject
from apps.institutions.models import Institution


class EightFourFourEngineTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.engine = EightFourFourEngine()

    def _subject(self):
        return create_subject(
            institution=self.institution,
            subject_catalog_id=uuid.uuid4(),
            name="Mathematics",
            code="MATH",
        )


class EightFourFourEngineSatisfiesContractsTests(EightFourFourEngineTestCase):
    def test_is_an_assessment_engine_and_a_report_engine(self):
        self.assertIsInstance(self.engine, AssessmentEngine)
        self.assertIsInstance(self.engine, ReportEngine)


class EightFourFourEngineDelegationTests(EightFourFourEngineTestCase):
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
                "exam_type": "cat",
                "score": 55,
                "max_score": 100,
            },
        )

        self.assertEqual(result["exam_type"], "cat")

    def test_compute_result_falls_back_to_a_live_unranked_calculation(self):
        subject = self._subject()
        student_id = uuid.uuid4()
        term_id = uuid.uuid4()
        self.engine.record_assessment(
            institution=self.institution,
            student_id=student_id,
            term_id=term_id,
            details={
                "subject_id": str(subject.id),
                "exam_type": "cat",
                "score": 80,
                "max_score": 100,
            },
        )

        with bind_institution(self.institution):
            result = self.engine.compute_result(
                institution=self.institution, student_id=student_id, term_id=term_id
            )

        self.assertEqual(Decimal(result["mean_score"]), Decimal("80"))
        self.assertIsNone(result["rank_in_class"])

    def test_generate_report_data_delegates_to_selectors(self):
        student_id = uuid.uuid4()
        term_id = uuid.uuid4()

        with bind_institution(self.institution):
            data = self.engine.generate_report_data(
                institution=self.institution, student_id=student_id, term_id=term_id
            )

        self.assertEqual(data["exam_results"], [])

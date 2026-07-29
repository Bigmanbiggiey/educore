import uuid

from django.test import TestCase

from apps.core.context import bind_institution
from apps.curriculum_cbc.models import Competency, ContinuousAssessment, LearningArea, Project
from apps.curriculum_cbc.selectors import compute_term_result, get_report_data
from apps.institutions.models import Institution


class CurriculumCbcSelectorTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.ctx = bind_institution(self.institution)
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)

        self.learning_area = LearningArea.objects.create(
            institution_id=self.institution.id,
            subject_catalog_id=uuid.uuid4(),
            name="Environmental Activities",
            code="ENV",
        )
        self.competency = Competency.objects.create(
            institution_id=self.institution.id,
            learning_area=self.learning_area,
            strand="Weather",
            sub_strand="Sunny and rainy days",
        )
        self.student_id = uuid.uuid4()
        self.term_id = uuid.uuid4()


class ComputeTermResultTests(CurriculumCbcSelectorTestCase):
    def test_returns_the_most_common_performance_level_per_learning_area(self):
        other_competency = Competency.objects.create(
            institution_id=self.institution.id, learning_area=self.learning_area, strand="Seasons"
        )
        ContinuousAssessment.objects.create(
            institution_id=self.institution.id,
            student_id=self.student_id,
            competency=self.competency,
            term_id=self.term_id,
            performance_level=ContinuousAssessment.PerformanceLevel.EXCEEDING_EXPECTATION,
        )
        ContinuousAssessment.objects.create(
            institution_id=self.institution.id,
            student_id=self.student_id,
            competency=other_competency,
            term_id=self.term_id,
            performance_level=ContinuousAssessment.PerformanceLevel.MEETING_EXPECTATION,
        )

        result = compute_term_result(self.institution, self.student_id, self.term_id)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["learning_area_name"], "Environmental Activities")

    def test_returns_empty_list_when_nothing_assessed(self):
        self.assertEqual(compute_term_result(self.institution, self.student_id, self.term_id), [])


class GetReportDataTests(CurriculumCbcSelectorTestCase):
    def test_includes_competencies_and_projects(self):
        ContinuousAssessment.objects.create(
            institution_id=self.institution.id,
            student_id=self.student_id,
            competency=self.competency,
            term_id=self.term_id,
            performance_level=ContinuousAssessment.PerformanceLevel.MEETING_EXPECTATION,
            evidence_notes="Drew a rain cloud",
        )
        Project.objects.create(
            institution_id=self.institution.id,
            student_id=self.student_id,
            competency=self.competency,
            term_id=self.term_id,
            description="Weather chart",
        )

        data = get_report_data(self.institution, self.student_id, self.term_id)

        self.assertEqual(len(data["learning_areas"]), 1)
        self.assertEqual(data["learning_areas"][0]["learning_area"], "Environmental Activities")
        self.assertEqual(
            data["learning_areas"][0]["competencies"][0]["performance_level"], "meeting_expectation"
        )
        self.assertEqual(len(data["projects"]), 1)

import uuid

from django.test import TestCase

from apps.academics.models import GradingScale
from apps.core.context import bind_institution
from apps.curriculum_844.models import ExamResult, Subject
from apps.curriculum_844.selectors import compute_mean_and_grade, get_report_data
from apps.institutions.models import Institution, InstitutionCurriculum

_EIGHT_FOUR_FOUR = InstitutionCurriculum.CurriculumType.EIGHT_FOUR_FOUR


class Curriculum844SelectorTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.ctx = bind_institution(self.institution)
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)

        self.subject = Subject.objects.create(
            institution_id=self.institution.id,
            subject_catalog_id=uuid.uuid4(),
            name="Mathematics",
            code="MATH",
        )
        self.student_id = uuid.uuid4()
        self.term_id = uuid.uuid4()


class ComputeMeanAndGradeTests(Curriculum844SelectorTestCase):
    def test_returns_none_when_no_results_exist(self):
        mean_score, mean_grade = compute_mean_and_grade(
            self.institution, self.student_id, self.term_id
        )
        self.assertIsNone(mean_score)
        self.assertIsNone(mean_grade)

    def test_computes_an_unweighted_mean_percentage(self):
        ExamResult.objects.create(
            institution_id=self.institution.id,
            student_id=self.student_id,
            subject=self.subject,
            term_id=self.term_id,
            exam_type=ExamResult.ExamType.CAT,
            score="30.00",
            max_score="30.00",
        )
        other_subject = Subject.objects.create(
            institution_id=self.institution.id,
            subject_catalog_id=uuid.uuid4(),
            name="English",
            code="ENG",
        )
        ExamResult.objects.create(
            institution_id=self.institution.id,
            student_id=self.student_id,
            subject=other_subject,
            term_id=self.term_id,
            exam_type=ExamResult.ExamType.CAT,
            score="50.00",
            max_score="100.00",
        )

        mean_score, _mean_grade = compute_mean_and_grade(
            self.institution, self.student_id, self.term_id
        )

        self.assertEqual(mean_score, 75)

    def test_resolves_the_grade_from_the_institutions_grading_scale(self):
        GradingScale.objects.create(
            institution_id=self.institution.id,
            curriculum_type=_EIGHT_FOUR_FOUR,
            levels=[
                {"label": "A", "min": 80, "max": 100},
                {"label": "B", "min": 60, "max": 79.99},
                {"label": "C", "min": 0, "max": 59.99},
            ],
        )
        ExamResult.objects.create(
            institution_id=self.institution.id,
            student_id=self.student_id,
            subject=self.subject,
            term_id=self.term_id,
            exam_type=ExamResult.ExamType.CAT,
            score="70.00",
            max_score="100.00",
        )

        _mean_score, mean_grade = compute_mean_and_grade(
            self.institution, self.student_id, self.term_id
        )

        self.assertEqual(mean_grade, "B")


class GetReportDataTests(Curriculum844SelectorTestCase):
    def test_includes_exam_results(self):
        ExamResult.objects.create(
            institution_id=self.institution.id,
            student_id=self.student_id,
            subject=self.subject,
            term_id=self.term_id,
            exam_type=ExamResult.ExamType.END_TERM,
            score="65.00",
            max_score="100.00",
        )

        data = get_report_data(self.institution, self.student_id, self.term_id)

        self.assertEqual(len(data["exam_results"]), 1)
        self.assertEqual(data["exam_results"][0]["subject"], "Mathematics")
        self.assertIsNone(data["mean_score"])

import uuid

from django.test import TestCase

from apps.academics.models import GradingScale
from apps.classes_streams.models import AcademicYear, Term
from apps.core.context import bind_institution
from apps.curriculum_british.models import Coursework, PredictedGrade, Subject
from apps.curriculum_british.selectors import compute_mean_coursework_grade, get_report_data
from apps.institutions.models import Institution, InstitutionCurriculum

_BRITISH = InstitutionCurriculum.CurriculumType.BRITISH


class CurriculumBritishSelectorTestCase(TestCase):
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
        self.academic_year = AcademicYear.objects.create(
            institution_id=self.institution.id,
            year_label="2026",
            start_date="2026-01-01",
            end_date="2026-12-31",
        )
        self.term = Term.objects.create(
            institution_id=self.institution.id,
            academic_year=self.academic_year,
            name="Term 1",
            start_date="2026-01-01",
            end_date="2026-04-01",
        )
        self.student_id = uuid.uuid4()


class ComputeMeanCourseworkGradeTests(CurriculumBritishSelectorTestCase):
    def test_returns_none_when_no_coursework_exists(self):
        mean_score, mean_grade = compute_mean_coursework_grade(
            self.institution, self.student_id, self.term.id
        )
        self.assertIsNone(mean_score)
        self.assertIsNone(mean_grade)

    def test_resolves_the_grade_from_the_institutions_grading_scale(self):
        GradingScale.objects.create(
            institution_id=self.institution.id,
            curriculum_type=_BRITISH,
            levels=[
                {"label": "A*", "min": 90, "max": 100},
                {"label": "B", "min": 60, "max": 89.99},
                {"label": "C", "min": 0, "max": 59.99},
            ],
        )
        Coursework.objects.create(
            institution_id=self.institution.id,
            student_id=self.student_id,
            subject=self.subject,
            term_id=self.term.id,
            component="Unit 1",
            score="70.00",
            max_score="100.00",
        )

        _mean_score, mean_grade = compute_mean_coursework_grade(
            self.institution, self.student_id, self.term.id
        )

        self.assertEqual(mean_grade, "B")


class GetReportDataTests(CurriculumBritishSelectorTestCase):
    def test_includes_coursework_and_predicted_grades(self):
        Coursework.objects.create(
            institution_id=self.institution.id,
            student_id=self.student_id,
            subject=self.subject,
            term_id=self.term.id,
            component="Unit 1",
            score="65.00",
            max_score="100.00",
        )
        PredictedGrade.objects.create(
            institution_id=self.institution.id,
            student_id=self.student_id,
            subject=self.subject,
            academic_year_id=self.academic_year.id,
            predicted_grade="A",
            set_by=uuid.uuid4(),
        )

        data = get_report_data(self.institution, self.student_id, self.term.id)

        self.assertEqual(len(data["courseworks"]), 1)
        self.assertEqual(data["courseworks"][0]["subject"], "Mathematics")
        self.assertEqual(len(data["predicted_grades"]), 1)
        self.assertEqual(data["predicted_grades"][0]["predicted_grade"], "A")

    def test_returns_empty_predicted_grades_for_an_unknown_term(self):
        data = get_report_data(self.institution, self.student_id, uuid.uuid4())
        self.assertEqual(data["predicted_grades"], [])

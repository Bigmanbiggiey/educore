import uuid

from django.test import TestCase

from apps.academics.models import GradingScale
from apps.core.context import bind_institution
from apps.curriculum_tvet.models import (
    Certificate,
    CompetencyUnit,
    Course,
    IndustrialAttachment,
    PracticalAssessment,
    TVETDepartment,
)
from apps.curriculum_tvet.selectors import compute_mean_practical_score, get_report_data
from apps.institutions.models import Institution, InstitutionCurriculum

_TVET = InstitutionCurriculum.CurriculumType.TVET


class CurriculumTvetSelectorTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.ctx = bind_institution(self.institution)
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)

        department = TVETDepartment.objects.create(
            institution_id=self.institution.id, name="Engineering"
        )
        self.course = Course.objects.create(
            institution_id=self.institution.id,
            department=department,
            course_code="ENG101",
            name="Automotive Engineering",
        )
        self.competency_unit = CompetencyUnit.objects.create(
            institution_id=self.institution.id,
            course=self.course,
            unit_code="CU101",
            name="Engine Repair",
            credit_hours=10,
        )
        self.student_id = uuid.uuid4()
        self.term_id = uuid.uuid4()


class ComputeMeanPracticalScoreTests(CurriculumTvetSelectorTestCase):
    def test_returns_none_when_nothing_recorded(self):
        mean_score, mean_grade = compute_mean_practical_score(
            self.institution, self.student_id, self.term_id
        )
        self.assertIsNone(mean_score)
        self.assertIsNone(mean_grade)

    def test_resolves_the_grade_from_the_institutions_grading_scale(self):
        GradingScale.objects.create(
            institution_id=self.institution.id,
            curriculum_type=_TVET,
            levels=[
                {"label": "Distinction", "min": 80, "max": 100},
                {"label": "Credit", "min": 60, "max": 79.99},
                {"label": "Pass", "min": 0, "max": 59.99},
            ],
        )
        PracticalAssessment.objects.create(
            institution_id=self.institution.id,
            student_id=self.student_id,
            competency_unit=self.competency_unit,
            term_id=self.term_id,
            assessment_type=PracticalAssessment.AssessmentType.WORKSHOP,
            score="70.00",
            max_score="100.00",
            assessor_id=uuid.uuid4(),
        )

        _mean_score, mean_grade = compute_mean_practical_score(
            self.institution, self.student_id, self.term_id
        )

        self.assertEqual(mean_grade, "Credit")


class GetReportDataTests(CurriculumTvetSelectorTestCase):
    def test_includes_assessments_attachments_and_certificates(self):
        PracticalAssessment.objects.create(
            institution_id=self.institution.id,
            student_id=self.student_id,
            competency_unit=self.competency_unit,
            term_id=self.term_id,
            assessment_type=PracticalAssessment.AssessmentType.PRACTICAL_EXAM,
            score="65.00",
            max_score="100.00",
            assessor_id=uuid.uuid4(),
        )
        IndustrialAttachment.objects.create(
            institution_id=self.institution.id,
            student_id=self.student_id,
            host_organization="Acme Motors",
            start_date="2026-01-01",
            end_date="2026-03-01",
        )
        Certificate.objects.create(
            institution_id=self.institution.id,
            student_id=self.student_id,
            course=self.course,
            certificate_number="CERT-001",
        )

        data = get_report_data(self.institution, self.student_id, self.term_id)

        self.assertEqual(len(data["practical_assessments"]), 1)
        self.assertEqual(len(data["industrial_attachments"]), 1)
        self.assertEqual(len(data["certificates"]), 1)
        self.assertEqual(data["certificates"][0]["certificate_number"], "CERT-001")

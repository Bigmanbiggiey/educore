from django.test import TestCase

from apps.academics.services import create_grading_scale, create_subject
from apps.institutions.models import Institution, InstitutionCurriculum


class AcademicsServiceTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")


class CreateGradingScaleTests(AcademicsServiceTestCase):
    def test_creates_and_scopes_to_institution(self):
        scale = create_grading_scale(
            institution=self.institution,
            curriculum_type=InstitutionCurriculum.CurriculumType.CBC,
            levels=[{"label": "Exceeding Expectation", "min": 80, "max": 100}],
        )
        self.assertEqual(scale.institution_id, self.institution.id)
        self.assertEqual(len(scale.levels), 1)

    def test_rejects_an_unknown_curriculum_type(self):
        with self.assertRaises(ValueError):
            create_grading_scale(institution=self.institution, curriculum_type="klingon")


class CreateSubjectTests(AcademicsServiceTestCase):
    def test_creates_and_scopes_to_institution(self):
        subject = create_subject(
            institution=self.institution,
            curriculum_type=InstitutionCurriculum.CurriculumType.CBC,
            name="Mathematics",
            code="MATH",
        )
        self.assertEqual(subject.institution_id, self.institution.id)

    def test_rejects_an_unknown_curriculum_type(self):
        with self.assertRaises(ValueError):
            create_subject(
                institution=self.institution, curriculum_type="klingon", name="X", code="X"
            )

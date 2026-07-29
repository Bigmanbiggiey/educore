from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.academics.models import GradingScale, SubjectCatalog
from apps.core.context import bind_institution
from apps.institutions.models import Institution, InstitutionCurriculum


class AcademicsTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.ctx = bind_institution(self.institution)
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)


class GradingScaleConstraintTests(AcademicsTestCase):
    def test_unique_per_institution_and_curriculum(self):
        GradingScale.objects.create(
            institution_id=self.institution.id,
            curriculum_type=InstitutionCurriculum.CurriculumType.CBC,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                GradingScale.objects.create(
                    institution_id=self.institution.id,
                    curriculum_type=InstitutionCurriculum.CurriculumType.CBC,
                )

    def test_levels_defaults_to_empty_list(self):
        scale = GradingScale.objects.create(
            institution_id=self.institution.id,
            curriculum_type=InstitutionCurriculum.CurriculumType.CBC,
        )
        self.assertEqual(scale.levels, [])


class SubjectCatalogConstraintTests(AcademicsTestCase):
    def test_unique_code_per_institution_and_curriculum(self):
        SubjectCatalog.objects.create(
            institution_id=self.institution.id,
            curriculum_type=InstitutionCurriculum.CurriculumType.CBC,
            name="Mathematics",
            code="MATH",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SubjectCatalog.objects.create(
                    institution_id=self.institution.id,
                    curriculum_type=InstitutionCurriculum.CurriculumType.CBC,
                    name="Maths Again",
                    code="MATH",
                )

    def test_same_code_different_curriculum_is_allowed(self):
        SubjectCatalog.objects.create(
            institution_id=self.institution.id,
            curriculum_type=InstitutionCurriculum.CurriculumType.CBC,
            name="Mathematics",
            code="MATH",
        )
        SubjectCatalog.objects.create(
            institution_id=self.institution.id,
            curriculum_type=InstitutionCurriculum.CurriculumType.EIGHT_FOUR_FOUR,
            name="Mathematics",
            code="MATH",
        )  # must not raise

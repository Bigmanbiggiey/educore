from django.test import TestCase

from apps.academics.models import GradingScale, SubjectCatalog
from apps.academics.selectors import get_curriculum_engine, get_grading_scale, get_subject_catalog
from apps.core.context import bind_institution
from apps.institutions.models import Institution, InstitutionCurriculum


class AcademicsSelectorTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.ctx = bind_institution(self.institution)
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)


class GetGradingScaleTests(AcademicsSelectorTestCase):
    def test_returns_the_matching_scale(self):
        scale = GradingScale.objects.create(
            institution_id=self.institution.id,
            curriculum_type=InstitutionCurriculum.CurriculumType.CBC,
        )
        self.assertEqual(
            get_grading_scale(self.institution, InstitutionCurriculum.CurriculumType.CBC), scale
        )

    def test_returns_none_when_no_scale_exists(self):
        self.assertIsNone(
            get_grading_scale(self.institution, InstitutionCurriculum.CurriculumType.CBC)
        )


class GetSubjectCatalogTests(AcademicsSelectorTestCase):
    def test_filters_by_curriculum_type_when_given(self):
        cbc_subject = SubjectCatalog.objects.create(
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
        )

        result = get_subject_catalog(
            self.institution, InstitutionCurriculum.CurriculumType.CBC
        )

        self.assertEqual(list(result), [cbc_subject])

    def test_returns_everything_when_no_curriculum_type_given(self):
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
        )

        self.assertEqual(get_subject_catalog(self.institution).count(), 2)


class GetCurriculumEngineTests(AcademicsSelectorTestCase):
    def test_raises_not_implemented(self):
        """Genuine stub — no curriculum plugin registry exists until
        Phase 3 (docs/roadmap.md)."""
        with self.assertRaises(NotImplementedError):
            get_curriculum_engine(self.institution, InstitutionCurriculum.CurriculumType.CBC)

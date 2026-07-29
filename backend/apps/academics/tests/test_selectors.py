import uuid

from django.test import TestCase

from apps.academics import registry
from apps.academics.contracts import AssessmentEngine, ReportEngine
from apps.academics.models import GradingScale, SubjectCatalog
from apps.academics.selectors import (
    get_curriculum_engine,
    get_curriculum_type_for_student,
    get_grading_scale,
    get_subject_catalog,
)
from apps.classes_streams.models import AcademicYear, ClassGrade, Term
from apps.core.context import bind_institution
from apps.institutions.models import Institution, InstitutionCurriculum
from apps.students.models import Enrollment, Student

_CBC = InstitutionCurriculum.CurriculumType.CBC
_EIGHT_FOUR_FOUR = InstitutionCurriculum.CurriculumType.EIGHT_FOUR_FOUR


class _DummyEngine(AssessmentEngine, ReportEngine):
    """A throwaway engine registered only for this test file — proves the
    resolver works without `academics` ever importing a real curriculum_*
    app (docs/modules.md's Layer 2 inversion)."""

    def record_assessment(self, *, institution, student_id, term_id, details):
        return {"recorded": True}

    def compute_result(self, *, institution, student_id, term_id):
        return {"result": "ok"}

    def generate_report_data(self, *, institution, student_id, term_id):
        return {"report": "ok"}


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

        result = get_subject_catalog(self.institution, InstitutionCurriculum.CurriculumType.CBC)

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
    def setUp(self):
        super().setUp()
        # Swap the real registry contents out for the duration of this test
        # class, so it's independent of whichever real curriculum_* apps
        # happen to be installed, and restore them afterward.
        self._saved_registry = dict(registry._registry)
        registry._registry.clear()
        registry.register(_CBC, _DummyEngine)
        self.addCleanup(self._restore_registry)

    def _restore_registry(self):
        registry._registry.clear()
        registry._registry.update(self._saved_registry)

    def test_resolves_a_registered_engine_for_an_explicit_curriculum_type(self):
        InstitutionCurriculum.objects.create(
            institution=self.institution, curriculum_type=_CBC, is_active=True
        )
        engine = get_curriculum_engine(self.institution, _CBC)
        self.assertIsInstance(engine, _DummyEngine)

    def test_resolves_without_curriculum_type_when_exactly_one_is_active(self):
        InstitutionCurriculum.objects.create(
            institution=self.institution, curriculum_type=_CBC, is_active=True
        )
        engine = get_curriculum_engine(self.institution)
        self.assertIsInstance(engine, _DummyEngine)

    def test_raises_when_curriculum_type_omitted_and_institution_runs_several(self):
        InstitutionCurriculum.objects.create(
            institution=self.institution, curriculum_type=_CBC, is_active=True
        )
        InstitutionCurriculum.objects.create(
            institution=self.institution, curriculum_type=_EIGHT_FOUR_FOUR, is_active=True
        )
        with self.assertRaises(ValueError):
            get_curriculum_engine(self.institution)

    def test_raises_when_the_institution_does_not_have_that_curriculum_active(self):
        with self.assertRaises(ValueError):
            get_curriculum_engine(self.institution, _CBC)

    def test_raises_when_nothing_is_registered_for_an_active_curriculum(self):
        InstitutionCurriculum.objects.create(
            institution=self.institution, curriculum_type=_EIGHT_FOUR_FOUR, is_active=True
        )
        with self.assertRaises(ValueError):
            get_curriculum_engine(self.institution, _EIGHT_FOUR_FOUR)


class GetCurriculumTypeForStudentTests(AcademicsSelectorTestCase):
    def _enrolled_student(self, curriculum_type):
        year = AcademicYear.objects.create(
            institution_id=self.institution.id,
            year_label="2026",
            start_date="2026-01-01",
            end_date="2026-12-31",
        )
        term = Term.objects.create(
            institution_id=self.institution.id,
            academic_year=year,
            name="Term 1",
            start_date="2026-01-01",
            end_date="2026-04-01",
        )
        class_grade = ClassGrade.objects.create(
            institution_id=self.institution.id,
            term=term,
            name="Grade 4",
            curriculum_type=curriculum_type,
        )
        student = Student.objects.create(
            institution_id=self.institution.id,
            admission_number="ADM-1",
            first_name="A",
            last_name="B",
        )
        Enrollment.objects.create(
            institution_id=self.institution.id,
            student=student,
            class_grade_id=class_grade.id,
            term_id=term.id,
        )
        return student, term

    def test_returns_the_class_grades_curriculum_type(self):
        student, term = self._enrolled_student(_CBC)
        self.assertEqual(get_curriculum_type_for_student(self.institution, student, term.id), _CBC)

    def test_returns_none_when_the_student_has_no_active_enrollment(self):
        student = Student.objects.create(
            institution_id=self.institution.id,
            admission_number="ADM-2",
            first_name="A",
            last_name="B",
        )
        self.assertIsNone(get_curriculum_type_for_student(self.institution, student, uuid.uuid4()))

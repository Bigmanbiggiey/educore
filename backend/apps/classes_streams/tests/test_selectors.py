import uuid

from django.test import TestCase

from apps.classes_streams.models import AcademicYear, ClassGrade, Term
from apps.classes_streams.selectors import get_class_grade, get_current_term, get_term
from apps.core.context import bind_institution, current_institution
from apps.institutions.models import Institution, InstitutionCurriculum


class GetCurrentTermTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")

    def test_returns_none_with_no_current_term(self):
        self.assertIsNone(get_current_term(self.institution))

    def test_returns_the_current_term(self):
        with bind_institution(self.institution):
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
                is_current=True,
            )

        self.assertEqual(get_current_term(self.institution), term)

    def test_works_with_no_ambient_tenant_context_bound(self):
        """Must not depend on TenantMiddleware having already bound a
        context — a future Celery task calls this with no request in
        progress at all (docs/authentication.md §7)."""
        self.assertIsNone(current_institution.get())
        self.assertIsNone(get_current_term(self.institution))
        self.assertIsNone(current_institution.get())  # unchanged afterward


class GetClassGradeTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        with bind_institution(self.institution):
            year = AcademicYear.objects.create(
                institution_id=self.institution.id,
                year_label="2026",
                start_date="2026-01-01",
                end_date="2026-12-31",
            )
            self.term = Term.objects.create(
                institution_id=self.institution.id,
                academic_year=year,
                name="Term 1",
                start_date="2026-01-01",
                end_date="2026-04-01",
            )

    def test_returns_the_class_grade(self):
        with bind_institution(self.institution):
            class_grade = ClassGrade.objects.create(
                institution_id=self.institution.id,
                term=self.term,
                name="Grade 4",
                curriculum_type=InstitutionCurriculum.CurriculumType.CBC,
            )

        self.assertEqual(get_class_grade(self.institution, class_grade.id), class_grade)

    def test_returns_none_for_a_different_institutions_class_grade(self):
        other = Institution.objects.create(name="Kiambu High", slug="kiambu-high")
        with bind_institution(self.institution):
            class_grade = ClassGrade.objects.create(
                institution_id=self.institution.id,
                term=self.term,
                name="Grade 4",
                curriculum_type=InstitutionCurriculum.CurriculumType.CBC,
            )

        self.assertIsNone(get_class_grade(other, class_grade.id))


class GetTermTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        with bind_institution(self.institution):
            year = AcademicYear.objects.create(
                institution_id=self.institution.id,
                year_label="2026",
                start_date="2026-01-01",
                end_date="2026-12-31",
            )
            self.term = Term.objects.create(
                institution_id=self.institution.id,
                academic_year=year,
                name="Term 1",
                start_date="2026-01-01",
                end_date="2026-04-01",
            )

    def test_returns_the_term(self):
        self.assertEqual(get_term(self.institution, self.term.id), self.term)

    def test_returns_none_for_an_unknown_term(self):
        self.assertIsNone(get_term(self.institution, uuid.uuid4()))

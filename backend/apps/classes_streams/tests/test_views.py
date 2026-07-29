from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.classes_streams.models import AcademicYear, Term
from apps.core.context import bind_institution
from apps.institutions.models import Domain, Institution
from apps.permissions.models import (
    InstitutionMembership,
    MembershipRole,
    Permission,
    Role,
    RolePermission,
)

HOSTNAME = "st-mary.educore.africa"


class ClassesStreamsAPITestCase(APITestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        Domain.objects.create(
            institution=self.institution,
            hostname=HOSTNAME,
            domain_type=Domain.DomainType.SUBDOMAIN,
            is_primary=True,
        )
        self.user = User.objects.create_user(email="teacher@stmary.ac.ke", password="x" * 12)
        self.membership = InstitutionMembership.objects.create(
            user=self.user, institution=self.institution
        )
        self.client.credentials(HTTP_AUTHORIZATION=self._bearer(self.user))

    def _bearer(self, user):
        return f"Bearer {RefreshToken.for_user(user).access_token}"

    def _grant(self, code):
        role = Role.objects.create(name="Test Role", institution=self.institution)
        permission = Permission.objects.create(code=code)
        RolePermission.objects.create(role=role, permission=permission)
        MembershipRole.objects.create(membership=self.membership, role=role)


class AcademicYearViewSetTests(ClassesStreamsAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:classes_streams:academic-year-list")

    def test_any_active_member_can_list(self):
        response = self.client.get(self.url, HTTP_HOST=HOSTNAME)
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_request_is_rejected(self):
        self.client.credentials()
        response = self.client.get(self.url, HTTP_HOST=HOSTNAME)
        self.assertEqual(response.status_code, 401)

    def test_create_without_permission_is_denied(self):
        response = self.client.post(
            self.url,
            {"year_label": "2026", "start_date": "2026-01-01", "end_date": "2026-12-31"},
            HTTP_HOST=HOSTNAME,
        )
        self.assertEqual(response.status_code, 403)

    def test_create_with_permission_succeeds(self):
        self._grant("classes_streams.academic_year.manage")

        response = self.client.post(
            self.url,
            {"year_label": "2026", "start_date": "2026-01-01", "end_date": "2026-12-31"},
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)
        with bind_institution(self.institution):
            year = AcademicYear.objects.get()
        self.assertEqual(year.institution_id, self.institution.id)

    def test_institution_id_in_the_request_body_is_ignored(self):
        """docs/api-design.md §7: there is no institution_id parameter
        anywhere in the API — it's always resolved server-side."""
        self._grant("classes_streams.academic_year.manage")
        other = Institution.objects.create(name="Kiambu High", slug="kiambu-high")

        self.client.post(
            self.url,
            {
                "year_label": "2026",
                "start_date": "2026-01-01",
                "end_date": "2026-12-31",
                "institution_id": str(other.id),
            },
            HTTP_HOST=HOSTNAME,
        )

        with bind_institution(self.institution):
            year = AcademicYear.objects.get()
        self.assertEqual(year.institution_id, self.institution.id)


class TermSetCurrentActionTests(ClassesStreamsAPITestCase):
    def setUp(self):
        super().setUp()
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
        self.url = reverse("v1:classes_streams:term-set-current", kwargs={"pk": self.term.pk})

    def test_denied_without_permission(self):
        response = self.client.post(self.url, HTTP_HOST=HOSTNAME)
        self.assertEqual(response.status_code, 403)

    def test_sets_the_term_current_with_permission(self):
        self._grant("classes_streams.term.manage")

        response = self.client.post(self.url, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 200)
        self.term.refresh_from_db()
        self.assertTrue(self.term.is_current)

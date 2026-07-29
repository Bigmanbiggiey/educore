from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.institutions.models import Domain, Institution
from apps.permissions.models import (
    InstitutionMembership,
    MembershipRole,
    Permission,
    Role,
    RolePermission,
)

HOSTNAME = "st-mary.educore.africa"


class AcademicsAPITestCase(APITestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        Domain.objects.create(
            institution=self.institution,
            hostname=HOSTNAME,
            domain_type=Domain.DomainType.SUBDOMAIN,
            is_primary=True,
        )
        self.user = User.objects.create_user(email="member@stmary.ac.ke", password="x" * 12)
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


class SubjectCatalogViewSetTests(AcademicsAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:academics:subject-list")

    def test_any_active_member_can_list(self):
        response = self.client.get(self.url, HTTP_HOST=HOSTNAME)
        self.assertEqual(response.status_code, 200)

    def test_create_without_permission_is_denied(self):
        response = self.client.post(
            self.url,
            {"curriculum_type": "cbc", "name": "Mathematics", "code": "MATH"},
            HTTP_HOST=HOSTNAME,
        )
        self.assertEqual(response.status_code, 403)

    def test_create_with_permission_succeeds(self):
        self._grant("academics.subject_catalog.manage")

        response = self.client.post(
            self.url,
            {"curriculum_type": "cbc", "name": "Mathematics", "code": "MATH"},
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)


class GradingScaleViewSetTests(AcademicsAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:academics:grading-scale-list")

    def test_create_with_permission_succeeds(self):
        self._grant("academics.grading_scale.manage")

        response = self.client.post(
            self.url,
            {"curriculum_type": "cbc", "levels": [{"label": "EE", "min": 80, "max": 100}]},
            format="json",
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)

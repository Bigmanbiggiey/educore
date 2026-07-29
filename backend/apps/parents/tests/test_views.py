import uuid

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.core.context import bind_institution
from apps.institutions.models import Domain, Institution
from apps.parents.models import ParentProfile
from apps.permissions.models import (
    InstitutionMembership,
    MembershipRole,
    Permission,
    Role,
    RolePermission,
)

HOSTNAME = "st-mary.educore.africa"


class ParentsAPITestCase(APITestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        Domain.objects.create(
            institution=self.institution,
            hostname=HOSTNAME,
            domain_type=Domain.DomainType.SUBDOMAIN,
            is_primary=True,
        )
        self.user = User.objects.create_user(email="parent@stmary.ac.ke", password="x" * 12)
        self.membership = InstitutionMembership.objects.create(
            user=self.user, institution=self.institution
        )
        self.client.credentials(HTTP_AUTHORIZATION=self._bearer(self.user))

    def _bearer(self, user):
        return f"Bearer {RefreshToken.for_user(user).access_token}"

    def _grant_role(self, role_name, *, permission_codes=()):
        role = Role.objects.create(name=role_name, institution=self.institution)
        for code in permission_codes:
            permission = Permission.objects.create(code=code)
            RolePermission.objects.create(role=role, permission=permission)
        MembershipRole.objects.create(membership=self.membership, role=role)


class ParentProfileViewSetTests(ParentsAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:parents:parent-profile-list")

    def test_no_permission_is_denied(self):
        response = self.client.get(self.url, HTTP_HOST=HOSTNAME)
        self.assertEqual(response.status_code, 403)

    def test_parent_only_sees_their_own_profile_even_with_broad_permission(self):
        self._grant_role("Parent", permission_codes=["parents.parent_profile.manage"])
        with bind_institution(self.institution):
            own_profile = ParentProfile.objects.create(
                institution_id=self.institution.id, user_id=self.user.id
            )
            ParentProfile.objects.create(
                institution_id=self.institution.id, user_id=uuid.uuid4()
            )

        response = self.client.get(self.url, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], str(own_profile.id))

    def test_create_with_permission_succeeds(self):
        self._grant_role("Registrar", permission_codes=["parents.parent_profile.manage"])

        response = self.client.post(
            self.url,
            {"user_id": str(self.user.id), "preferred_language": "sw"},
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["preferred_language"], "sw")

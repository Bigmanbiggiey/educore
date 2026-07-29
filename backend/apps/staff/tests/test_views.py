import uuid

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.core.context import bind_institution
from apps.institutions.models import Domain, Institution
from apps.permissions.models import (
    InstitutionMembership,
    MembershipRole,
    Permission,
    Role,
    RolePermission,
)
from apps.staff.models import StaffProfile

HOSTNAME = "st-mary.educore.africa"


class StaffAPITestCase(APITestCase):
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


class StaffProfileViewSetTests(StaffAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:staff:staff-profile-list")

    def test_no_permission_is_denied(self):
        response = self.client.get(self.url, HTTP_HOST=HOSTNAME)
        self.assertEqual(response.status_code, 403)

    def test_create_with_permission_succeeds(self):
        self._grant("staff.staff_profile.manage")

        response = self.client.post(
            self.url,
            {
                "user_id": str(uuid.uuid4()),
                "employee_number": "EMP-001",
                "first_name": "Jane",
                "last_name": "Teacher",
                "employment_type": "full_time",
            },
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)

    def test_institution_id_in_the_request_body_is_ignored(self):
        self._grant("staff.staff_profile.manage")
        other = Institution.objects.create(name="Kiambu High", slug="kiambu-high")

        response = self.client.post(
            self.url,
            {
                "user_id": str(uuid.uuid4()),
                "employee_number": "EMP-001",
                "first_name": "Jane",
                "last_name": "Teacher",
                "employment_type": "full_time",
                "institution_id": str(other.id),
            },
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.data["id"] is not None, True)
        with bind_institution(self.institution):
            staff = StaffProfile.objects.get()
        self.assertEqual(staff.institution_id, self.institution.id)

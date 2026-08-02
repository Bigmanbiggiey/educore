import uuid

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


class ClinicAPITestCase(APITestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        Domain.objects.create(
            institution=self.institution,
            hostname=HOSTNAME,
            domain_type=Domain.DomainType.SUBDOMAIN,
            is_primary=True,
        )
        self.user = User.objects.create_user(email="nurse@stmary.ac.ke", password="x" * 12)
        self.membership = InstitutionMembership.objects.create(
            user=self.user, institution=self.institution
        )
        self.client.credentials(HTTP_AUTHORIZATION=self._bearer(self.user))

    def _bearer(self, user):
        return f"Bearer {RefreshToken.for_user(user).access_token}"

    def _grant(self, code):
        # `get_or_create` rather than `create`: some tests grant more than
        # one permission code in a single test (e.g. `view` then `manage`),
        # and `Role.name` is unique per institution.
        role, _ = Role.objects.get_or_create(name="Test Role", institution=self.institution)
        permission = Permission.objects.create(code=code)
        RolePermission.objects.create(role=role, permission=permission)
        MembershipRole.objects.get_or_create(membership=self.membership, role=role)


class HealthRecordViewSetTests(ClinicAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:clinic:health-record-list")

    def test_reads_are_denied_to_a_plain_active_member(self):
        # Unlike every other Layer 1 app, mere institution membership is
        # *not* enough here — reads require clinic.health_record.view too.
        response = self.client.get(self.url, HTTP_HOST=HOSTNAME)
        self.assertEqual(response.status_code, 403)

    def test_reads_succeed_once_granted_the_view_permission(self):
        self._grant("clinic.health_record.view")
        response = self.client.get(self.url, HTTP_HOST=HOSTNAME)
        self.assertEqual(response.status_code, 200)

    def test_write_requires_the_manage_permission_not_just_view(self):
        self._grant("clinic.health_record.view")
        response = self.client.post(
            self.url,
            {"student_id": str(uuid.uuid4()), "allergies": "Peanuts"},
            HTTP_HOST=HOSTNAME,
        )
        self.assertEqual(response.status_code, 403)

    def test_set_health_record_with_manage_permission_succeeds(self):
        self._grant("clinic.health_record.manage")
        student_id = str(uuid.uuid4())

        response = self.client.post(
            self.url, {"student_id": student_id, "allergies": "Peanuts"}, HTTP_HOST=HOSTNAME
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["allergies"], "Peanuts")

    def test_resetting_the_same_student_updates_in_place(self):
        # Both permissions granted upfront — `get_membership_access` is
        # Redis-cached per user/institution (docs/permissions.md §6), so
        # granting mid-test after a request has already been made would
        # read a stale cached bundle, same pitfall `library`'s test suite
        # hit first.
        self._grant("clinic.health_record.manage")
        self._grant("clinic.health_record.view")
        student_id = str(uuid.uuid4())
        self.client.post(
            self.url, {"student_id": student_id, "allergies": "Peanuts"}, HTTP_HOST=HOSTNAME
        )

        response = self.client.post(
            self.url, {"student_id": student_id, "allergies": "Dust"}, HTTP_HOST=HOSTNAME
        )

        self.assertEqual(response.status_code, 201)
        list_response = self.client.get(self.url, HTTP_HOST=HOSTNAME)
        self.assertEqual(list_response.data["count"], 1)
        self.assertEqual(list_response.data["results"][0]["allergies"], "Dust")


class ClinicVisitViewSetTests(ClinicAPITestCase):
    def test_reads_denied_without_permission(self):
        response = self.client.get(reverse("v1:clinic:clinic-visit-list"), HTTP_HOST=HOSTNAME)
        self.assertEqual(response.status_code, 403)

    def test_create_with_permission_succeeds(self):
        self._grant("clinic.clinic_visit.manage")
        response = self.client.post(
            reverse("v1:clinic:clinic-visit-list"),
            {
                "student_id": str(uuid.uuid4()),
                "visit_date": "2026-02-01",
                "treated_by_id": str(uuid.uuid4()),
                "notes": "Fever",
            },
            HTTP_HOST=HOSTNAME,
        )
        self.assertEqual(response.status_code, 201)

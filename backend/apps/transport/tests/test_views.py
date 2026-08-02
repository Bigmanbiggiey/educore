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
from apps.transport.models import Route, Stop, Vehicle

HOSTNAME = "st-mary.educore.africa"


class TransportAPITestCase(APITestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        Domain.objects.create(
            institution=self.institution,
            hostname=HOSTNAME,
            domain_type=Domain.DomainType.SUBDOMAIN,
            is_primary=True,
        )
        self.user = User.objects.create_user(email="ops@stmary.ac.ke", password="x" * 12)
        self.membership = InstitutionMembership.objects.create(
            user=self.user, institution=self.institution
        )
        self.client.credentials(HTTP_AUTHORIZATION=self._bearer(self.user))
        with bind_institution(self.institution):
            self.vehicle = Vehicle.objects.create(
                institution_id=self.institution.id, registration_number="KDA 001A", capacity=30
            )
            self.route = Route.objects.create(
                institution_id=self.institution.id, vehicle=self.vehicle, name="Route A"
            )
            self.stop = Stop.objects.create(
                institution_id=self.institution.id, route=self.route, name="Gate", sequence=1
            )

    def _bearer(self, user):
        return f"Bearer {RefreshToken.for_user(user).access_token}"

    def _grant(self, code):
        role, _ = Role.objects.get_or_create(name="Test Role", institution=self.institution)
        permission = Permission.objects.create(code=code)
        RolePermission.objects.create(role=role, permission=permission)
        MembershipRole.objects.get_or_create(membership=self.membership, role=role)


class TransportAssignmentViewSetTests(TransportAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:transport:transport-assignment-list")

    def test_assign_without_permission_is_denied(self):
        response = self.client.post(
            self.url,
            {
                "student_id": str(uuid.uuid4()),
                "route": str(self.route.id),
                "stop": str(self.stop.id),
            },
            HTTP_HOST=HOSTNAME,
        )
        self.assertEqual(response.status_code, 403)

    def test_assign_with_permission_succeeds(self):
        self._grant("transport.transport_assignment.manage")
        student_id = str(uuid.uuid4())

        response = self.client.post(
            self.url,
            {"student_id": student_id, "route": str(self.route.id), "stop": str(self.stop.id)},
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)

    def test_reassigning_updates_in_place(self):
        self._grant("transport.transport_assignment.manage")
        student_id = str(uuid.uuid4())
        self.client.post(
            self.url,
            {"student_id": student_id, "route": str(self.route.id), "stop": str(self.stop.id)},
            HTTP_HOST=HOSTNAME,
        )

        response = self.client.post(
            self.url,
            {"student_id": student_id, "route": str(self.route.id), "stop": str(self.stop.id)},
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)
        list_response = self.client.get(self.url, {"student_id": student_id}, HTTP_HOST=HOSTNAME)
        self.assertEqual(list_response.data["count"], 1)


class RouteManifestActionTests(TransportAPITestCase):
    def test_manifest_reflects_assigned_students(self):
        self._grant("transport.transport_assignment.manage")
        student_id = str(uuid.uuid4())
        self.client.post(
            reverse("v1:transport:transport-assignment-list"),
            {"student_id": student_id, "route": str(self.route.id), "stop": str(self.stop.id)},
            HTTP_HOST=HOSTNAME,
        )

        response = self.client.get(
            reverse("v1:transport:route-manifest", kwargs={"pk": self.route.id}), HTTP_HOST=HOSTNAME
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["student_ids"], [student_id])

import uuid

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.core.context import bind_institution
from apps.hostel.models import Hostel, Room
from apps.institutions.models import Domain, Institution
from apps.permissions.models import (
    InstitutionMembership,
    MembershipRole,
    Permission,
    Role,
    RolePermission,
)

HOSTNAME = "st-mary.educore.africa"


class HostelAPITestCase(APITestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        Domain.objects.create(
            institution=self.institution,
            hostname=HOSTNAME,
            domain_type=Domain.DomainType.SUBDOMAIN,
            is_primary=True,
        )
        self.user = User.objects.create_user(email="warden@stmary.ac.ke", password="x" * 12)
        self.membership = InstitutionMembership.objects.create(
            user=self.user, institution=self.institution
        )
        self.client.credentials(HTTP_AUTHORIZATION=self._bearer(self.user))
        with bind_institution(self.institution):
            self.hostel = Hostel.objects.create(institution_id=self.institution.id, name="Block A")
            self.room = Room.objects.create(
                institution_id=self.institution.id,
                hostel=self.hostel,
                room_number="101",
                capacity=1,
            )
        self.term_id = str(uuid.uuid4())

    def _bearer(self, user):
        return f"Bearer {RefreshToken.for_user(user).access_token}"

    def _grant(self, code):
        role, _ = Role.objects.get_or_create(name="Test Role", institution=self.institution)
        permission = Permission.objects.create(code=code)
        RolePermission.objects.create(role=role, permission=permission)
        MembershipRole.objects.get_or_create(membership=self.membership, role=role)


class BedAllocationViewSetTests(HostelAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:hostel:bed-allocation-list")

    def test_allocate_without_permission_is_denied(self):
        response = self.client.post(
            self.url,
            {"room": str(self.room.id), "student_id": str(uuid.uuid4()), "term_id": self.term_id},
            HTTP_HOST=HOSTNAME,
        )
        self.assertEqual(response.status_code, 403)

    def test_allocate_with_permission_succeeds(self):
        self._grant("hostel.bed_allocation.manage")

        response = self.client.post(
            self.url,
            {"room": str(self.room.id), "student_id": str(uuid.uuid4()), "term_id": self.term_id},
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)

    def test_allocation_past_capacity_is_rejected(self):
        self._grant("hostel.bed_allocation.manage")
        self.client.post(
            self.url,
            {"room": str(self.room.id), "student_id": str(uuid.uuid4()), "term_id": self.term_id},
            HTTP_HOST=HOSTNAME,
        )

        response = self.client.post(
            self.url,
            {"room": str(self.room.id), "student_id": str(uuid.uuid4()), "term_id": self.term_id},
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 400)


class RoomOccupancyActionTests(HostelAPITestCase):
    def test_occupancy_requires_term_id(self):
        response = self.client.get(
            reverse("v1:hostel:room-occupancy", kwargs={"pk": self.room.id}), HTTP_HOST=HOSTNAME
        )
        self.assertEqual(response.status_code, 400)

    def test_occupancy_reflects_allocations(self):
        self._grant("hostel.bed_allocation.manage")
        self.client.post(
            reverse("v1:hostel:bed-allocation-list"),
            {"room": str(self.room.id), "student_id": str(uuid.uuid4()), "term_id": self.term_id},
            HTTP_HOST=HOSTNAME,
        )

        response = self.client.get(
            reverse("v1:hostel:room-occupancy", kwargs={"pk": self.room.id}),
            {"term_id": self.term_id},
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"capacity": 1, "occupied": 1, "available": 0})

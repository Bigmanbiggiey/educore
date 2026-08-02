from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.core.context import bind_institution
from apps.institutions.models import Domain, Institution
from apps.inventory.models import StockItem
from apps.permissions.models import (
    InstitutionMembership,
    MembershipRole,
    Permission,
    Role,
    RolePermission,
)

HOSTNAME = "st-mary.educore.africa"


class InventoryAPITestCase(APITestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        Domain.objects.create(
            institution=self.institution,
            hostname=HOSTNAME,
            domain_type=Domain.DomainType.SUBDOMAIN,
            is_primary=True,
        )
        self.user = User.objects.create_user(email="storekeeper@stmary.ac.ke", password="x" * 12)
        self.membership = InstitutionMembership.objects.create(
            user=self.user, institution=self.institution
        )
        self.client.credentials(HTTP_AUTHORIZATION=self._bearer(self.user))
        with bind_institution(self.institution):
            self.item = StockItem.objects.create(institution_id=self.institution.id, name="Chalk")

    def _bearer(self, user):
        return f"Bearer {RefreshToken.for_user(user).access_token}"

    def _grant(self, code):
        role = Role.objects.create(name="Test Role", institution=self.institution)
        permission = Permission.objects.create(code=code)
        RolePermission.objects.create(role=role, permission=permission)
        MembershipRole.objects.create(membership=self.membership, role=role)


class StockMovementViewSetTests(InventoryAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:inventory:stock-movement-list")

    def test_record_movement_without_permission_is_denied(self):
        response = self.client.post(
            self.url,
            {"stock_item": str(self.item.id), "direction": "in", "quantity": 5},
            HTTP_HOST=HOSTNAME,
        )
        self.assertEqual(response.status_code, 403)

    def test_record_movement_with_permission_updates_stock_level(self):
        self._grant("inventory.stock_movement.manage")

        response = self.client.post(
            self.url,
            {"stock_item": str(self.item.id), "direction": "in", "quantity": 5},
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity_on_hand, 5)

    def test_out_movement_exceeding_stock_is_rejected(self):
        self._grant("inventory.stock_movement.manage")

        response = self.client.post(
            self.url,
            {"stock_item": str(self.item.id), "direction": "out", "quantity": 1},
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 400)

    def test_filter_by_direction(self):
        self._grant("inventory.stock_movement.manage")
        self.client.post(
            self.url,
            {"stock_item": str(self.item.id), "direction": "in", "quantity": 5},
            HTTP_HOST=HOSTNAME,
        )
        self.client.post(
            self.url,
            {"stock_item": str(self.item.id), "direction": "out", "quantity": 2},
            HTTP_HOST=HOSTNAME,
        )

        response = self.client.get(self.url, {"direction": "out"}, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)


class StockItemViewSetTests(InventoryAPITestCase):
    def test_quantity_on_hand_is_not_directly_writable(self):
        self._grant("inventory.stock_item.manage")

        response = self.client.patch(
            reverse("v1:inventory:stock-item-detail", kwargs={"pk": self.item.id}),
            {"quantity_on_hand": 999},
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity_on_hand, 0)

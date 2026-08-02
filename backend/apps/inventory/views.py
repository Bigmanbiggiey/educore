"""API views for `inventory` — docs/api-design.md. `StockMovement` creation
routes through `services.record_movement` (has to check available stock on
an "out" movement and update `StockItem.quantity_on_hand` alongside the
write — the generic create path can't do that, same reasoning as
`library.LoanViewSet`).
"""

from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from api.viewsets import TenantScopedModelViewSet
from apps.inventory import services
from apps.inventory.filters import StockMovementFilterSet
from apps.inventory.models import Asset, StockItem, StockMovement, Supplier
from apps.inventory.serializers import (
    AssetSerializer,
    StockItemSerializer,
    StockMovementSerializer,
    SupplierSerializer,
)
from apps.permissions.permissions import HasPermission, IsInstitutionMember

_WRITE_ACTIONS = ("create", "update", "partial_update", "destroy")


def _write_gated_by(permission_code):
    def get_permissions(self):
        if self.action in _WRITE_ACTIONS:
            return [IsInstitutionMember(), HasPermission(permission_code)()]
        return [IsInstitutionMember()]

    return get_permissions


class SupplierViewSet(TenantScopedModelViewSet):
    queryset_model = Supplier
    serializer_class = SupplierSerializer
    get_permissions = _write_gated_by("inventory.supplier.manage")


class AssetViewSet(TenantScopedModelViewSet):
    queryset_model = Asset
    serializer_class = AssetSerializer
    get_permissions = _write_gated_by("inventory.asset.manage")


class StockItemViewSet(TenantScopedModelViewSet):
    queryset_model = StockItem
    serializer_class = StockItemSerializer
    get_permissions = _write_gated_by("inventory.stock_item.manage")


class StockMovementViewSet(TenantScopedModelViewSet):
    queryset_model = StockMovement
    serializer_class = StockMovementSerializer
    filterset_class = StockMovementFilterSet
    get_permissions = _write_gated_by("inventory.stock_movement.manage")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            movement = services.record_movement(
                institution=request.institution, **serializer.validated_data
            )
        except ValueError as exc:
            raise ValidationError({"detail": [str(exc)]}) from exc
        return Response(self.get_serializer(movement).data, status=201)

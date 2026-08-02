"""Request/response shapes for `inventory`'s API surface — docs/api-design.md.
`StockItem.quantity_on_hand` is read-only — it only ever changes via
`StockMovementViewSet`, never a direct `PATCH`, same convention
`library.Copy.status` established for a service-managed field... except
`Copy.status` stayed writable there since it also needs direct correction
outside any dedicated action (see that serializer's own history); here
there genuinely is one single sanctioned write path (`record_movement`),
same shape as `Loan.returned_at`.
"""

from api.serializers import TenantScopedModelSerializer
from apps.inventory.models import Asset, StockItem, StockMovement, Supplier


class SupplierSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Supplier
        fields = [
            "id",
            "name",
            "contact_person",
            "phone",
            "email",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AssetSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Asset
        fields = [
            "id",
            "name",
            "category",
            "serial_number",
            "status",
            "supplier",
            "acquired_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class StockItemSerializer(TenantScopedModelSerializer):
    class Meta:
        model = StockItem
        fields = [
            "id",
            "name",
            "unit",
            "quantity_on_hand",
            "supplier",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "quantity_on_hand", "created_at", "updated_at"]


class StockMovementSerializer(TenantScopedModelSerializer):
    class Meta:
        model = StockMovement
        fields = [
            "id",
            "stock_item",
            "direction",
            "quantity",
            "reason",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

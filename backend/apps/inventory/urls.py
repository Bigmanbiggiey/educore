from rest_framework.routers import DefaultRouter

from apps.inventory.views import (
    AssetViewSet,
    StockItemViewSet,
    StockMovementViewSet,
    SupplierViewSet,
)

app_name = "inventory"

router = DefaultRouter()
router.register("suppliers", SupplierViewSet, basename="supplier")
router.register("assets", AssetViewSet, basename="asset")
router.register("stock-items", StockItemViewSet, basename="stock-item")
router.register("stock-movements", StockMovementViewSet, basename="stock-movement")

urlpatterns = router.urls

from rest_framework.routers import DefaultRouter

from apps.transport.views import (
    RouteViewSet,
    StopViewSet,
    TransportAssignmentViewSet,
    VehicleViewSet,
)

app_name = "transport"

router = DefaultRouter()
router.register("vehicles", VehicleViewSet, basename="vehicle")
router.register("routes", RouteViewSet, basename="route")
router.register("stops", StopViewSet, basename="stop")
router.register(
    "transport-assignments", TransportAssignmentViewSet, basename="transport-assignment"
)

urlpatterns = router.urls

from rest_framework.routers import DefaultRouter

from apps.hostel.views import BedAllocationViewSet, HostelViewSet, RoomViewSet

app_name = "hostel"

router = DefaultRouter()
router.register("hostels", HostelViewSet, basename="hostel")
router.register("rooms", RoomViewSet, basename="room")
router.register("bed-allocations", BedAllocationViewSet, basename="bed-allocation")

urlpatterns = router.urls

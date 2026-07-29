from rest_framework.routers import DefaultRouter

from apps.staff.views import StaffProfileViewSet

app_name = "staff"

router = DefaultRouter()
router.register("staff", StaffProfileViewSet, basename="staff-profile")

urlpatterns = router.urls

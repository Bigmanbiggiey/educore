from rest_framework.routers import DefaultRouter

from apps.attendance.views import AttendanceRecordViewSet

app_name = "attendance"

router = DefaultRouter()
router.register("attendance", AttendanceRecordViewSet, basename="attendance-record")

urlpatterns = router.urls

from rest_framework.routers import DefaultRouter

from apps.students.views import EnrollmentViewSet, GuardianRelationshipViewSet, StudentViewSet

app_name = "students"

router = DefaultRouter()
router.register("students", StudentViewSet, basename="student")
router.register("enrollments", EnrollmentViewSet, basename="enrollment")
router.register(
    "guardian-relationships", GuardianRelationshipViewSet, basename="guardian-relationship"
)

urlpatterns = router.urls

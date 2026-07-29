from rest_framework.routers import DefaultRouter

from apps.classes_streams.views import (
    AcademicYearViewSet,
    ClassGradeViewSet,
    ClassTeacherAssignmentViewSet,
    StreamViewSet,
    TermViewSet,
)

app_name = "classes_streams"

router = DefaultRouter()
router.register("academic-years", AcademicYearViewSet, basename="academic-year")
router.register("terms", TermViewSet, basename="term")
router.register("class-grades", ClassGradeViewSet, basename="class-grade")
router.register("streams", StreamViewSet, basename="stream")
router.register(
    "class-teacher-assignments", ClassTeacherAssignmentViewSet, basename="class-teacher-assignment"
)

urlpatterns = router.urls

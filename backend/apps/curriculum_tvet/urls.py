from rest_framework.routers import DefaultRouter

from apps.curriculum_tvet.views import (
    CertificateViewSet,
    CompetencyUnitViewSet,
    CourseViewSet,
    IndustrialAttachmentViewSet,
    TVETDepartmentViewSet,
)

app_name = "curriculum_tvet"

router = DefaultRouter()
router.register("departments", TVETDepartmentViewSet, basename="department")
router.register("courses", CourseViewSet, basename="course")
router.register("competency-units", CompetencyUnitViewSet, basename="competency-unit")
router.register(
    "industrial-attachments", IndustrialAttachmentViewSet, basename="industrial-attachment"
)
router.register("certificates", CertificateViewSet, basename="certificate")

urlpatterns = router.urls

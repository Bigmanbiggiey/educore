from rest_framework.routers import DefaultRouter

from apps.clinic.views import ClinicVisitViewSet, HealthRecordViewSet, MedicationViewSet

app_name = "clinic"

router = DefaultRouter()
router.register("health-records", HealthRecordViewSet, basename="health-record")
router.register("clinic-visits", ClinicVisitViewSet, basename="clinic-visit")
router.register("medications", MedicationViewSet, basename="medication")

urlpatterns = router.urls

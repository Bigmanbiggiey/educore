from rest_framework.routers import DefaultRouter

from apps.institutions.views import DomainViewSet, InstitutionViewSet

app_name = "institutions"

router = DefaultRouter()
router.register("institutions", InstitutionViewSet, basename="institution")
router.register("domains", DomainViewSet, basename="domain")

urlpatterns = router.urls

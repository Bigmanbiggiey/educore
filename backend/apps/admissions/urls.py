from rest_framework.routers import DefaultRouter

from apps.admissions.views import ApplicationViewSet

app_name = "admissions"

router = DefaultRouter()
router.register("applications", ApplicationViewSet, basename="application")

urlpatterns = router.urls

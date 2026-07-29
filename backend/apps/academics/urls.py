from rest_framework.routers import DefaultRouter

from apps.academics.views import GradingScaleViewSet, SubjectCatalogViewSet

app_name = "academics"

router = DefaultRouter()
router.register("grading-scales", GradingScaleViewSet, basename="grading-scale")
router.register("subjects", SubjectCatalogViewSet, basename="subject")

urlpatterns = router.urls

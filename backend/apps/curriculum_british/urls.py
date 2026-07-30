from rest_framework.routers import DefaultRouter

from apps.curriculum_british.views import PredictedGradeViewSet, SubjectViewSet, YearGroupViewSet

app_name = "curriculum_british"

router = DefaultRouter()
router.register("year-groups", YearGroupViewSet, basename="year-group")
router.register("subjects", SubjectViewSet, basename="subject")
router.register("predicted-grades", PredictedGradeViewSet, basename="predicted-grade")

urlpatterns = router.urls

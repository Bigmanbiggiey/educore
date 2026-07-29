from rest_framework.routers import DefaultRouter

from apps.curriculum_cbc.views import (
    CompetencyViewSet,
    CoreValueViewSet,
    LearningAreaViewSet,
    PCIViewSet,
    ProjectViewSet,
)

app_name = "curriculum_cbc"

router = DefaultRouter()
router.register("learning-areas", LearningAreaViewSet, basename="learning-area")
router.register("competencies", CompetencyViewSet, basename="competency")
router.register("core-values", CoreValueViewSet, basename="core-value")
router.register("pcis", PCIViewSet, basename="pci")
router.register("projects", ProjectViewSet, basename="project")

urlpatterns = router.urls

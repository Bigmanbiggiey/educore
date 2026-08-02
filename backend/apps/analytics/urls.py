from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.analytics.views import (
    AttendanceRateSnapshotViewSet,
    FeeCollectionSnapshotViewSet,
    MeanGradeRollupViewSet,
    RecomputeRollupsView,
)

app_name = "analytics"

router = DefaultRouter()
router.register("attendance-rollups", AttendanceRateSnapshotViewSet, basename="attendance-rollup")
router.register(
    "fee-collection-rollups", FeeCollectionSnapshotViewSet, basename="fee-collection-rollup"
)
router.register("mean-grade-rollups", MeanGradeRollupViewSet, basename="mean-grade-rollup")

urlpatterns = [
    *router.urls,
    path("analytics/recompute/", RecomputeRollupsView.as_view(), name="recompute-rollups"),
]

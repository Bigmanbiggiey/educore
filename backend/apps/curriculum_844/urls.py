from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.curriculum_844.views import (
    KcpeKcseResultImportView,
    RecomputeMeanGradesView,
    SubjectViewSet,
)

app_name = "curriculum_844"

router = DefaultRouter()
router.register("subjects", SubjectViewSet, basename="subject")

urlpatterns = [
    *router.urls,
    path("recompute-mean-grades/", RecomputeMeanGradesView.as_view(), name="recompute-mean-grades"),
    path("kcpe-kcse-results/import/", KcpeKcseResultImportView.as_view(), name="kcpe-kcse-import"),
]

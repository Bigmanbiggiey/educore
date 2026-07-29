from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.academics.views import (
    AssessmentRecordView,
    GradingScaleViewSet,
    ReportCardView,
    SubjectCatalogViewSet,
)

app_name = "academics"

router = DefaultRouter()
router.register("grading-scales", GradingScaleViewSet, basename="grading-scale")
router.register("subjects", SubjectCatalogViewSet, basename="subject")

urlpatterns = [
    *router.urls,
    path("assessments/", AssessmentRecordView.as_view(), name="assessment-record"),
    path(
        "report-cards/<uuid:student_id>/<uuid:term_id>/",
        ReportCardView.as_view(),
        name="report-card",
    ),
]

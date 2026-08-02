from django.urls import path

from apps.reports.views import GenerateClassReportCardsView, GenerateReportCardView

app_name = "reports"

urlpatterns = [
    path("report-cards/generate/", GenerateReportCardView.as_view(), name="generate-report-card"),
    path(
        "report-cards/generate-class/",
        GenerateClassReportCardsView.as_view(),
        name="generate-class-report-cards",
    ),
]

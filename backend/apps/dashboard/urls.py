from django.urls import path

from apps.dashboard.views import (
    ParentDashboardView,
    PrincipalDashboardView,
    StudentDashboardView,
    TeacherDashboardView,
)

app_name = "dashboard"

urlpatterns = [
    path("dashboard/principal/", PrincipalDashboardView.as_view(), name="principal"),
    path("dashboard/teacher/", TeacherDashboardView.as_view(), name="teacher"),
    path("dashboard/parent/", ParentDashboardView.as_view(), name="parent"),
    path("dashboard/student/", StudentDashboardView.as_view(), name="student"),
]

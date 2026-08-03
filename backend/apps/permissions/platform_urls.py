from django.urls import path

from apps.permissions.views import ActAsView, EndActAsView, PlatformLoginView

app_name = "permissions-platform"

urlpatterns = [
    path("auth/login/", PlatformLoginView.as_view(), name="platform-login"),
    path(
        "admin/act-as/<uuid:institution_id>/",
        ActAsView.as_view(),
        name="act-as",
    ),
    path("admin/act-as/end/", EndActAsView.as_view(), name="act-as-end"),
]

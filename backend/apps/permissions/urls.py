from django.urls import path

from apps.permissions.views import HostContextView, LoginView, LogoutView, MeView, RefreshView

app_name = "permissions"

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("host-context/", HostContextView.as_view(), name="host-context"),
    path("refresh/", RefreshView.as_view(), name="refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
]

"""`InviteMemberView`'s URL — kept separate from `permissions/urls.py`
(mounted at the session-only `auth/` prefix) and `platform_urls.py`
(platform-staff-only): this endpoint is institution-scoped, so it's
registered at the API root instead, alongside `students`/`staff`/`parents`.
"""

from django.urls import path

from apps.permissions.views import InviteMemberView

app_name = "permissions-members"

urlpatterns = [
    path("members/invite/", InviteMemberView.as_view(), name="member-invite"),
]

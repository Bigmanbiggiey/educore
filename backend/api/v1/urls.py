from django.urls import include, path

app_name = "v1"

urlpatterns = [
    # Both included under the same auth/ prefix: password-reset is
    # accounts-owned (no membership check needed); login/refresh/logout/me
    # are permissions-owned (docs/authentication.md §3's InstitutionMembership
    # check needs a dependency accounts doesn't have).
    path("auth/", include("apps.accounts.urls")),
    path("auth/", include("apps.permissions.urls")),
    path("", include("apps.classes_streams.urls")),
    path("", include("apps.students.urls")),
    path("", include("apps.staff.urls")),
    path("", include("apps.parents.urls")),
    path("", include("apps.academics.urls")),
    path("", include("apps.timetable.urls")),
    path("", include("apps.attendance.urls")),
    path("", include("apps.admissions.urls")),
]

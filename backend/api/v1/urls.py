from django.urls import include, path

from apps.finance.webhooks import MpesaCallbackView

app_name = "v1"

urlpatterns = [
    # Both included under the same auth/ prefix: password-reset is
    # accounts-owned (no membership check needed); login/refresh/logout/me
    # are permissions-owned (docs/authentication.md §3's InstitutionMembership
    # check needs a dependency accounts doesn't have).
    path("auth/", include("apps.accounts.urls")),
    path("auth/", include("apps.permissions.urls")),
    # docs/permissions.md §7: platform-staff endpoints, gated by
    # `is_platform_staff` rather than `InstitutionMembership`/`Role` — never
    # reachable via `TenantMiddleware`'s normal institution-Host resolution.
    path("platform/", include("apps.permissions.platform_urls")),
    path("platform/", include("apps.institutions.urls")),
    path("platform/", include("apps.audit.urls")),
    path("", include("apps.classes_streams.urls")),
    path("", include("apps.students.urls")),
    path("", include("apps.staff.urls")),
    path("", include("apps.parents.urls")),
    path("", include("apps.academics.urls")),
    path("", include("apps.timetable.urls")),
    path("", include("apps.attendance.urls")),
    path("", include("apps.admissions.urls")),
    # Curriculum plugins get their own hyphenated URL namespace, unlike the
    # flat Layer 0/1 apps above — docs/api-design.md §8: multiple future
    # curriculum apps will have colliding concept names like "Subject".
    path("curriculum-cbc/", include("apps.curriculum_cbc.urls")),
    path("curriculum-844/", include("apps.curriculum_844.urls")),
    path("curriculum-british/", include("apps.curriculum_british.urls")),
    path("curriculum-tvet/", include("apps.curriculum_tvet.urls")),
    path("curriculum-university/", include("apps.curriculum_university.urls")),
    path("", include("apps.finance.urls")),
    path("", include("apps.communication.urls")),
    path("", include("apps.library.urls")),
    path("", include("apps.inventory.urls")),
    path("", include("apps.clinic.urls")),
    path("", include("apps.documents.urls")),
    path("", include("apps.transport.urls")),
    path("", include("apps.hostel.urls")),
    path("", include("apps.analytics.urls")),
    path("", include("apps.reports.urls")),
    path("", include("apps.dashboard.urls")),
    # Outside TenantMiddleware's normal tenant resolution (Safaricom calls
    # back on the fixed public API host, not a per-institution subdomain —
    # see apps/finance/webhooks.py's module docstring) — institution_id and
    # stk_request_id are embedded in the URL itself instead.
    path(
        "webhooks/mpesa/callback/<uuid:institution_id>/<uuid:stk_request_id>/<str:token>/",
        MpesaCallbackView.as_view(),
        name="mpesa-callback",
    ),
]

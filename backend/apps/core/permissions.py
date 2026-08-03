"""`IsPlatformStaff` lives here, not in `apps.permissions` (where every
other reusable DRF permission class lives), for a real layering reason:
`apps.institutions`'s platform-management views (docs/permissions.md §7)
need it too, and `.importlinter`'s layer-0 contract fixes `institutions`
strictly below `permissions`/`audit` — importing it from `permissions`
would be a forbidden reverse dependency. `core` is the one layer every
other app already depends on, so it's the only valid shared home for a
permission class `institutions`, `permissions`, and `audit` all need.
"""

from rest_framework.permissions import BasePermission


class IsPlatformStaff(BasePermission):
    """Gates `docs/permissions.md` §7's platform-level endpoints
    (`/platform/...`) — `is_platform_staff` is a bare boolean on `User`,
    never institution-scoped, so this never reads `request.institution`."""

    def has_permission(self, request, view) -> bool:
        return bool(request.user.is_authenticated and request.user.is_platform_staff)

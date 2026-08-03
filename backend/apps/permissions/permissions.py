"""Reusable DRF permission classes `permissions` exposes for other apps'
`views.py` to compose (docs/modules.md, docs/permissions.md §6):

    permission_classes = [
        IsAuthenticated, IsInstitutionMember, HasPermission("finance.invoice.view"),
    ]

`request.institution` is set by `institutions.middleware.TenantMiddleware`
before any view runs; these classes read it rather than accepting an
institution as an argument, since it's never client-supplied
(docs/api-design.md §7).

This is RBAC only — the "object scope" layer (a Teacher restricted to
their own assigned classes, a Parent to their own children) is a separate
filter applied at the selector/queryset level by the owning app, not
folded in here (docs/permissions.md §3).
"""

from rest_framework.permissions import BasePermission

from apps.permissions.selectors import get_membership_access, is_institution_member


class IsInstitutionMember(BasePermission):
    def has_permission(self, request, view) -> bool:
        institution = getattr(request, "institution", None)
        if institution is None or not request.user.is_authenticated:
            return False
        # Break-glass session (docs/permissions.md §7): a System Admin
        # acting inside this institution's data for the duration of a
        # time-boxed act-as window, never a real InstitutionMembership.
        if getattr(request, "acting_as_admin", False):
            return True
        return is_institution_member(request.user, institution)


def HasRole(*role_names: str) -> type[BasePermission]:
    class _HasRole(BasePermission):
        def has_permission(self, request, view) -> bool:
            institution = getattr(request, "institution", None)
            if institution is None or not request.user.is_authenticated:
                return False
            if getattr(request, "acting_as_admin", False):
                return True
            access = get_membership_access(request.user, institution)
            return bool(access.role_names & set(role_names))

    return _HasRole


def HasPermission(code: str) -> type[BasePermission]:
    class _HasPermission(BasePermission):
        def has_permission(self, request, view) -> bool:
            institution = getattr(request, "institution", None)
            if institution is None or not request.user.is_authenticated:
                return False
            if getattr(request, "acting_as_admin", False):
                return True
            access = get_membership_access(request.user, institution)
            return code in access.permission_codes

    return _HasPermission

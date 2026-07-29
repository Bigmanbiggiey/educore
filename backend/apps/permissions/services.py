"""Public write interface for `permissions` — docs/modules.md. Other apps
mutate membership/role state only through these functions, never by
touching apps.permissions.models directly (docs/project-structure.md §3).
"""

from django.core.cache import cache
from django.db import transaction

from apps.accounts.models import User
from apps.institutions.models import Institution
from apps.permissions.models import (
    InstitutionMembership,
    MembershipRole,
    Permission,
    Role,
    RolePermission,
)
from apps.permissions.selectors import cache_key_for


def _invalidate_access_cache(membership: InstitutionMembership) -> None:
    """Explicit invalidation, not left to the 5-minute TTL — a role
    revocation during a security incident must take effect immediately
    (docs/permissions.md §6)."""
    cache.delete(cache_key_for(membership.user_id, membership.institution_id))


def create_membership(
    *, user: User, institution: Institution, is_default: bool = False
) -> InstitutionMembership:
    return InstitutionMembership.objects.create(
        user=user, institution=institution, is_default=is_default
    )


def assign_role(membership: InstitutionMembership, role: Role) -> MembershipRole:
    membership_role, _ = MembershipRole.objects.get_or_create(membership=membership, role=role)
    _invalidate_access_cache(membership)
    return membership_role


def revoke_role(membership: InstitutionMembership, role: Role) -> None:
    MembershipRole.objects.filter(membership=membership, role=role).delete()
    _invalidate_access_cache(membership)


@transaction.atomic
def grant_permission_to_role(role: Role, permission: Permission):
    """docs/permissions.md §1: platform-scoped permissions are never
    assignable to an institution-defined custom role — enforced here, at
    the write path, not just as a UI hint."""
    if permission.scope == Permission.Scope.PLATFORM and role.institution_id is not None:
        raise ValueError(
            "Platform-scoped permissions cannot be assigned to an institution-defined role"
        )
    role_permission, _ = RolePermission.objects.get_or_create(role=role, permission=permission)
    # A role's permission set changed — invalidate every active membership
    # holding this role, not just one user, since the cache key is keyed
    # per (user, institution) but the grant applies to everyone with the role.
    memberships = InstitutionMembership.objects.filter(roles=role).only("user_id", "institution_id")
    for membership in memberships:
        _invalidate_access_cache(membership)
    return role_permission

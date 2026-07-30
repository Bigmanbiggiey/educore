"""Public read interface for `permissions` — docs/modules.md.

`get_membership_access` is the one Redis-cached lookup docs/permissions.md
§6 describes: membership + role + permission are fetched and cached
together under a single `perm:{user_id}:{institution_id}` key, 5-minute
TTL, so both `HasRole` and `HasPermission` share one cache entry per
(user, institution) pair instead of issuing separate round trips.
"""

from __future__ import annotations

from typing import NamedTuple

from django.core.cache import cache

from apps.accounts.models import User
from apps.institutions.models import Institution
from apps.permissions.models import InstitutionMembership, Permission, Role

CACHE_TTL_SECONDS = 300


def cache_key_for(user_id, institution_id) -> str:
    """Shared with `services.py`'s cache-invalidation calls — the same key
    format must produce the same key on both the read and write side."""
    return f"perm:{user_id}:{institution_id}"


class MembershipAccess(NamedTuple):
    role_names: frozenset[str]
    permission_codes: frozenset[str]


def is_institution_member(user: User, institution: Institution) -> bool:
    return InstitutionMembership.objects.filter(
        user=user, institution=institution, status=InstitutionMembership.Status.ACTIVE
    ).exists()


def get_user_roles(user: User, institution: Institution):
    """Uncached — used for admin/management-facing reads, not the
    per-request permission check (that's `get_membership_access`)."""
    return Role.objects.filter(
        memberships__user=user,
        memberships__institution=institution,
        memberships__status=InstitutionMembership.Status.ACTIVE,
    )


def get_members_with_role(institution: Institution, role_name: str):
    """Reverse direction of `get_user_roles` — every actively-membered user
    holding `role_name` at this institution. Uncached (same reasoning as
    `get_user_roles`); the one real caller so far is
    `communication.services.publish_announcement` resolving a role-targeted
    Announcement's audience into actual recipients."""
    return User.objects.filter(
        institution_memberships__institution=institution,
        institution_memberships__status=InstitutionMembership.Status.ACTIVE,
        institution_memberships__roles__name=role_name,
    ).distinct()


def get_membership_access(user: User, institution: Institution) -> MembershipAccess:
    cache_key = cache_key_for(user.id, institution.id)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    membership = InstitutionMembership.objects.filter(
        user=user, institution=institution, status=InstitutionMembership.Status.ACTIVE
    ).first()
    if membership is None:
        access = MembershipAccess(role_names=frozenset(), permission_codes=frozenset())
    else:
        access = MembershipAccess(
            role_names=frozenset(
                Role.objects.filter(memberships=membership).values_list("name", flat=True)
            ),
            permission_codes=frozenset(
                Permission.objects.filter(roles__memberships=membership).values_list(
                    "code", flat=True
                )
            ),
        )
    cache.set(cache_key, access, CACHE_TTL_SECONDS)
    return access

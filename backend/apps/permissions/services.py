"""Public write interface for `permissions` — docs/modules.md. Other apps
mutate membership/role state only through these functions, never by
touching apps.permissions.models directly (docs/project-structure.md §3).
"""

import secrets

from django.core.cache import cache
from django.db import transaction

from apps.accounts.models import User
from apps.accounts.services import register_user, request_password_reset
from apps.core.signals import audit_event, notification_requested
from apps.institutions.models import Institution
from apps.institutions.services import PLATFORM_DOMAIN_SUFFIX
from apps.permissions.models import (
    InstitutionMembership,
    MembershipRole,
    Permission,
    Role,
    RolePermission,
)
from apps.permissions.selectors import cache_key_for

INSTITUTION_ADMINISTRATOR_ROLE_NAME = "Institution Administrator"

# The 11 seeded system roles an Institution Administrator may invite a
# member into — everything from docs/permissions.md §2's 12 except
# "Institution Administrator" itself (auto-provisioned, see
# `provision_institution_admin` below) and "System Administrator" (not a
# `Role` at all — granted via `is_platform_staff`, docs/permissions.md §7).
INVITABLE_ROLE_NAMES = [
    "Principal",
    "Deputy Principal",
    "Finance Officer",
    "Teacher",
    "Parent",
    "Student",
    "Librarian",
    "Nurse",
    "Receptionist",
    "Transport Manager",
    "Hostel Warden",
]


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


def provision_institution_admin(
    *,
    institution: Institution,
    admin_email: str,
    admin_phone: str | None = None,
    actor: User | None = None,
) -> InstitutionMembership:
    """Seeds a freshly-provisioned Institution's first admin — the receiver
    for `apps.core.signals.institution_provisioned`
    (`apps.permissions.receivers`), called synchronously from inside
    `apps.institutions.services.provision_institution`'s own transaction.

    `permissions` is the one Layer 0 app that legally imports both
    `accounts` and `institutions` (`.importlinter`'s layer contract), which
    is why this orchestration lives here rather than in `institutions`
    itself.
    """
    if User.objects.filter(email=admin_email).exists():
        # Raised as ValueError, not left to surface as a bare IntegrityError
        # from register_user's save() — InstitutionViewSet.create already
        # catches ValueError and turns it into a clean 400, and this keeps
        # that working with no view-layer changes.
        raise ValueError(f"A user with email {admin_email!r} already exists")

    user = register_user(email=admin_email, phone=admin_phone, password=secrets.token_urlsafe(32))
    membership = create_membership(user=user, institution=institution, is_default=True)
    role = Role.objects.get(name=INSTITUTION_ADMINISTRATOR_ROLE_NAME, institution__isnull=True)
    assign_role(membership, role)
    reset_token = request_password_reset(user)

    audit_event.send(
        sender=provision_institution_admin,
        actor=actor,
        institution=institution,
        action="platform.institution.admin_provisioned",
        target=user,
    )
    notification_requested.send(
        sender=provision_institution_admin,
        institution=institution,
        recipient=user,
        template_key="institution_admin_welcome",
        context={
            "institution_name": institution.name,
            "reset_url": (
                f"https://{institution.slug}{PLATFORM_DOMAIN_SUFFIX}"
                f"/reset-password?token={reset_token.token}"
            ),
        },
        # Plain string, not notifications_core.models.Channel.EMAIL —
        # permissions/notifications_core are independent Layer 0 siblings
        # under `.importlinter`, so this app can't import that module.
        channel="email",
    )
    return membership


def invite_member(
    *,
    institution: Institution,
    role_name: str,
    email: str,
    phone: str | None = None,
    actor: User | None = None,
) -> InstitutionMembership:
    """Institution Administrator's onboarding path for the 11 non-admin
    seeded roles — same shape as `provision_institution_admin` above (that
    function's own docstring is why this orchestration lives here rather
    than in `staff`/`students`/`parents`: `.importlinter`'s layer contract
    forbids this Layer 0 app from importing any of those Layer 1 apps, so
    this stays a pure login+membership+role primitive; a role-specific
    profile — `StaffProfile`, `ParentProfile`, a `Student.user_id` — is a
    separate follow-up call to that app's own existing endpoint, not part
    of this function).
    """
    if role_name not in INVITABLE_ROLE_NAMES:
        raise ValueError(f"{role_name!r} is not an invitable role")

    if User.objects.filter(email=email).exists():
        raise ValueError(f"A user with email {email!r} already exists")

    user = register_user(email=email, phone=phone, password=secrets.token_urlsafe(32))
    membership = create_membership(user=user, institution=institution, is_default=True)
    role = Role.objects.get(name=role_name, institution__isnull=True, is_system=True)
    assign_role(membership, role)
    reset_token = request_password_reset(user)

    audit_event.send(
        sender=invite_member,
        actor=actor,
        institution=institution,
        action="permissions.membership.member_invited",
        target=user,
    )
    notification_requested.send(
        sender=invite_member,
        institution=institution,
        recipient=user,
        template_key="member_welcome",
        context={
            "institution_name": institution.name,
            "role_name": role_name,
            "reset_url": (
                f"https://{institution.slug}{PLATFORM_DOMAIN_SUFFIX}"
                f"/reset-password?token={reset_token.token}"
            ),
        },
        channel="email",
    )
    return membership


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

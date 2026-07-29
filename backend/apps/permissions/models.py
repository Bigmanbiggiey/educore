"""Layer 0 RBAC models — docs/database.md §2, docs/permissions.md.
`accounts` owns identity; this app owns the User↔Institution↔Role link and
the permission catalog, since a user can hold different roles at different
institutions (docs/modules.md's own rationale for the split).

`Role`/`InstitutionMembership` use real ForeignKeys to `Institution`, not
the plain-UUID `TenantScopedModel` pattern — like `institutions.Domain`,
this is Layer 0 data that always lives in the shared `default` database
regardless of any tenant's isolation tier (docs/multitenancy.md §4), so the
cross-database FK problem `TenantScopedModel` works around doesn't apply.
"""

from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel
from apps.institutions.models import Institution


class Role(TimeStampedModel):
    """`institution=None` marks a global template role (Teacher, Principal,
    …) seeded once at platform install and shared by every institution;
    `institution` set marks an institution-defined custom role (e.g. an
    "Exams Coordinator" role with no seeded template)."""

    institution = models.ForeignKey(
        Institution, null=True, blank=True, on_delete=models.CASCADE, related_name="roles"
    )
    name = models.CharField(max_length=100)
    # True for the 12 seeded portal-default roles (docs/permissions.md §2)
    # — prevents accidental deletion of a role real memberships depend on.
    is_system = models.BooleanField(default=False)
    permissions = models.ManyToManyField(
        "Permission", through="RolePermission", related_name="roles"
    )

    class Meta:
        pass

    # A nested `class Meta` can't see local names from the enclosing class
    # body (only module globals), so `constraints` is assigned here instead
    # of inside `Meta` itself — same pattern as apps.institutions.models.
    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution", "name"], name="role_unique_name_per_institution"
        ),
        # Postgres treats NULLs as distinct in a plain unique constraint, so
        # the constraint above alone wouldn't stop two global (institution
        # IS NULL) roles from sharing a name — this partial index closes
        # that gap, mirroring institutions.Domain's one-primary-per-institution
        # partial index.
        models.UniqueConstraint(
            fields=["name"],
            condition=models.Q(institution__isnull=True),
            name="role_unique_global_name",
        ),
    ]

    def __str__(self) -> str:
        return self.name if self.institution_id is None else f"{self.name} ({self.institution})"


class Permission(TimeStampedModel):
    """The full ~200+ permission-code catalog is generated per module at
    implementation time, named to match the `services.py` function each
    code gates (docs/permissions.md §1/§8) — this table is deliberately
    near-empty until then."""

    class Scope(models.TextChoices):
        PLATFORM = "platform", "Platform"
        INSTITUTION = "institution", "Institution"

    code = models.CharField(max_length=150, unique=True)
    description = models.CharField(max_length=255, blank=True, default="")
    # platform-scoped permissions are never assignable to an
    # institution-defined custom role — enforced in services.grant_permission_to_role,
    # not just a UI hint (docs/permissions.md §1).
    scope = models.CharField(max_length=20, choices=Scope.choices, default=Scope.INSTITUTION)

    class Meta:
        pass

    Meta.constraints = [
        models.CheckConstraint(
            condition=models.Q(scope__in=Scope.values), name="permission_valid_scope"
        ),
    ]

    def __str__(self) -> str:
        return self.code


class RolePermission(TimeStampedModel):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_permissions")
    permission = models.ForeignKey(
        Permission, on_delete=models.CASCADE, related_name="role_permissions"
    )

    class Meta:
        pass

    Meta.constraints = [
        models.UniqueConstraint(fields=["role", "permission"], name="unique_role_permission"),
    ]

    def __str__(self) -> str:
        return f"{self.role} — {self.permission}"


class InstitutionMembership(TimeStampedModel):
    """(user, institution) join row `accounts.User` deliberately doesn't
    own — roles are M2M off this row, not off the (user, institution) pair
    directly, so a person can hold multiple roles at one institution (a
    Deputy Principal who also teaches) without denormalizing a role list
    onto this model (docs/database.md §2)."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="institution_memberships"
    )
    institution = models.ForeignKey(
        Institution, on_delete=models.CASCADE, related_name="memberships"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    # Which membership a multi-institution user lands in post-login
    # (docs/database.md §2) — not enforced as at-most-one-per-user here;
    # `services.create_membership` owns that invariant.
    is_default = models.BooleanField(default=False)
    roles = models.ManyToManyField(Role, through="MembershipRole", related_name="memberships")

    class Meta:
        pass

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["user", "institution"], name="unique_membership_per_user_institution"
        ),
        models.CheckConstraint(
            condition=models.Q(status__in=Status.values), name="membership_valid_status"
        ),
    ]

    def __str__(self) -> str:
        return f"{self.user} @ {self.institution}"


class MembershipRole(TimeStampedModel):
    membership = models.ForeignKey(
        InstitutionMembership, on_delete=models.CASCADE, related_name="membership_roles"
    )
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="membership_roles")

    class Meta:
        pass

    Meta.constraints = [
        models.UniqueConstraint(fields=["membership", "role"], name="unique_membership_role"),
    ]

    def __str__(self) -> str:
        return f"{self.membership} — {self.role}"

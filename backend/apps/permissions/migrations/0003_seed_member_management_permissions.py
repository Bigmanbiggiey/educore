"""Seeds the `Permission`/`RolePermission` rows the new `InviteMemberView`
(and the already-existing `staff`/`parents`/`students` endpoints it hands
off to for role-specific profile creation) actually need to work.

Narrow by design, not an app-wide backfill: `Permission.objects.count()`
was confirmed to be exactly 0 in the live deployment before this
migration — every `HasPermission("...")`-gated view in the project
(`staff.staff_profile.manage`, `parents.parent_profile.manage`,
`students.student.manage`, `students.guardian_relationship.manage` among
them) has been silently unusable by anyone, including the one real
Institution Administrator. This migration seeds and grants only the 5
codes this feature's own end-to-end flow touches — inviting a member, then
optionally giving Teacher/Parent a profile or attaching a login to an
existing Student. Every other app's own missing permission grants are a
separate, deliberately out-of-scope gap (docs/permissions.md §8 already
names the full catalog as "generated per module at implementation time" —
this migration follows that same per-need pattern, just for this feature).
"""

from django.db import migrations

INSTITUTION_ADMINISTRATOR_ROLE_NAME = "Institution Administrator"

PERMISSION_CODES = [
    ("permissions.membership.invite", "Invite a member into this institution"),
    ("staff.staff_profile.manage", "Create/update/delete staff profiles"),
    ("parents.parent_profile.manage", "Create/update/delete parent profiles"),
    ("students.student.manage", "Create/update/delete students"),
    (
        "students.guardian_relationship.manage",
        "Link a guardian/parent to a student",
    ),
]


def seed_permissions(apps, schema_editor):
    Permission = apps.get_model("permissions", "Permission")
    Role = apps.get_model("permissions", "Role")
    RolePermission = apps.get_model("permissions", "RolePermission")

    admin_role = Role.objects.get(
        name=INSTITUTION_ADMINISTRATOR_ROLE_NAME, institution__isnull=True
    )
    for code, description in PERMISSION_CODES:
        permission, _ = Permission.objects.get_or_create(
            code=code, defaults={"description": description, "scope": "institution"}
        )
        RolePermission.objects.get_or_create(role=admin_role, permission=permission)


def unseed_permissions(apps, schema_editor):
    Permission = apps.get_model("permissions", "Permission")
    codes = [code for code, _ in PERMISSION_CODES]
    Permission.objects.filter(code__in=codes).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("permissions", "0002_seed_system_roles"),
    ]

    operations = [
        migrations.RunPython(seed_permissions, unseed_permissions),
    ]

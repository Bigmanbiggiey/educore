"""Seeds the 12 portal-default roles as global templates
(Role(is_system=True, institution=None)) — docs/permissions.md §2.

System Administrator is deliberately excluded: it's granted via
`accounts.User.is_platform_staff`, not an `InstitutionMembership`/`Role`
(docs/permissions.md §7's "break glass" model, not an ambient role), which
is also why the doc's own count is "12" despite listing 13 names — System
Administrator is the odd one out of that list.
"""

from django.db import migrations

SYSTEM_ROLE_NAMES = [
    "Institution Administrator",
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


def seed_system_roles(apps, schema_editor):
    Role = apps.get_model("permissions", "Role")
    Role.objects.bulk_create(
        Role(name=name, institution=None, is_system=True) for name in SYSTEM_ROLE_NAMES
    )


def unseed_system_roles(apps, schema_editor):
    Role = apps.get_model("permissions", "Role")
    Role.objects.filter(
        name__in=SYSTEM_ROLE_NAMES, institution__isnull=True, is_system=True
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("permissions", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_system_roles, unseed_system_roles),
    ]

"""Confirms the 0002 data migration's seeded roles actually exist post-migrate
— docs/permissions.md §2. This runs against the real migration history
(not a MigratorTestCase replay) since these rows are meant to already be
present by the time any test suite runs.
"""

from django.test import TestCase

from apps.permissions.models import Role

# Mirrors apps/permissions/migrations/0002_seed_system_roles.py's
# SYSTEM_ROLE_NAMES — duplicated rather than imported since migration
# modules have non-identifier names (leading digit) and aren't meant to be
# imported elsewhere; this list is a fixed historical record either way.
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


class SeedSystemRolesTests(TestCase):
    def test_all_twelve_system_roles_exist_as_global_templates(self):
        self.assertEqual(len(SYSTEM_ROLE_NAMES), 12)
        for name in SYSTEM_ROLE_NAMES:
            self.assertTrue(
                Role.objects.filter(name=name, institution__isnull=True, is_system=True).exists(),
                f"expected seeded global role {name!r}",
            )

    def test_system_administrator_is_not_a_seeded_role(self):
        """docs/permissions.md §7: System Administrator access is granted via
        `is_platform_staff`, not a Role — it's the one name in the doc's own
        13-item list that isn't part of the "12 portal roles" it seeds."""
        self.assertFalse(
            Role.objects.filter(name="System Administrator", institution__isnull=True).exists()
        )

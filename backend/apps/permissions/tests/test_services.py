from django.core.cache import cache
from django.test import TestCase

from apps.accounts.models import User
from apps.institutions.models import Institution
from apps.permissions.models import InstitutionMembership, MembershipRole, Permission, Role
from apps.permissions.selectors import get_membership_access
from apps.permissions.services import (
    assign_role,
    create_membership,
    grant_permission_to_role,
    revoke_role,
)


class CreateMembershipTests(TestCase):
    def test_creates_a_membership(self):
        institution = Institution.objects.create(name="St Mary", slug="st-mary")
        user = User.objects.create_user(email="teacher@stmary.ac.ke", password="x" * 12)

        membership = create_membership(user=user, institution=institution)

        self.assertEqual(membership.user, user)
        self.assertEqual(membership.institution, institution)
        self.assertFalse(membership.is_default)


class AssignRevokeRoleTests(TestCase):
    def setUp(self):
        cache.clear()
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.user = User.objects.create_user(email="teacher@stmary.ac.ke", password="x" * 12)
        self.membership = InstitutionMembership.objects.create(
            user=self.user, institution=self.institution
        )
        # Institution-scoped, not a global template — sidesteps collision
        # with the 12 seeded system roles (migration 0002).
        self.role = Role.objects.create(name="Teacher", institution=self.institution)

    def test_assign_role_creates_the_link(self):
        assign_role(self.membership, self.role)

        self.assertTrue(
            MembershipRole.objects.filter(membership=self.membership, role=self.role).exists()
        )

    def test_assign_role_is_idempotent(self):
        assign_role(self.membership, self.role)
        assign_role(self.membership, self.role)

        self.assertEqual(
            MembershipRole.objects.filter(membership=self.membership, role=self.role).count(), 1
        )

    def test_assign_role_invalidates_the_access_cache(self):
        get_membership_access(self.user, self.institution)  # warms the cache empty

        assign_role(self.membership, self.role)

        access = get_membership_access(self.user, self.institution)
        self.assertIn("Teacher", access.role_names)

    def test_revoke_role_removes_the_link_and_invalidates_the_cache(self):
        assign_role(self.membership, self.role)
        get_membership_access(self.user, self.institution)  # warms the cache with the role

        revoke_role(self.membership, self.role)

        access = get_membership_access(self.user, self.institution)
        self.assertNotIn("Teacher", access.role_names)


class GrantPermissionToRoleTests(TestCase):
    def test_grants_an_institution_scoped_permission_to_a_custom_role(self):
        institution = Institution.objects.create(name="St Mary", slug="st-mary")
        role = Role.objects.create(name="Exams Coordinator", institution=institution)
        permission = Permission.objects.create(
            code="academics.exam.schedule", scope=Permission.Scope.INSTITUTION
        )

        grant_permission_to_role(role, permission)

        self.assertIn(permission, role.permissions.all())

    def test_rejects_a_platform_scoped_permission_on_a_custom_role(self):
        institution = Institution.objects.create(name="St Mary", slug="st-mary")
        role = Role.objects.create(name="Exams Coordinator", institution=institution)
        permission = Permission.objects.create(
            code="institutions.institution.provision", scope=Permission.Scope.PLATFORM
        )

        with self.assertRaises(ValueError):
            grant_permission_to_role(role, permission)

    def test_allows_a_platform_scoped_permission_on_a_global_role(self):
        role = Role.objects.create(name="System Administrator", institution=None)
        permission = Permission.objects.create(
            code="institutions.institution.provision", scope=Permission.Scope.PLATFORM
        )

        grant_permission_to_role(role, permission)  # must not raise

        self.assertIn(permission, role.permissions.all())

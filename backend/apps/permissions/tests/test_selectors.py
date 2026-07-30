from django.core.cache import cache
from django.test import TestCase

from apps.accounts.models import User
from apps.institutions.models import Institution
from apps.permissions.models import (
    InstitutionMembership,
    MembershipRole,
    Permission,
    Role,
    RolePermission,
)
from apps.permissions.selectors import (
    get_members_with_role,
    get_membership_access,
    get_user_roles,
    is_institution_member,
)


class SelectorTests(TestCase):
    def setUp(self):
        cache.clear()
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.user = User.objects.create_user(email="teacher@stmary.ac.ke", password="x" * 12)
        # Institution-scoped, not a global template — sidesteps collision
        # with the 12 seeded system roles (migration 0002) while exercising
        # the same MembershipRole/RolePermission code paths.
        self.role = Role.objects.create(name="Teacher", institution=self.institution)
        self.permission = Permission.objects.create(code="attendance.record.create")
        RolePermission.objects.create(role=self.role, permission=self.permission)

    def _make_membership(self, **kwargs):
        return InstitutionMembership.objects.create(
            user=self.user, institution=self.institution, **kwargs
        )

    def test_is_institution_member_false_with_no_membership(self):
        self.assertFalse(is_institution_member(self.user, self.institution))

    def test_is_institution_member_true_for_active_membership(self):
        self._make_membership()
        self.assertTrue(is_institution_member(self.user, self.institution))

    def test_is_institution_member_false_for_suspended_membership(self):
        self._make_membership(status=InstitutionMembership.Status.SUSPENDED)
        self.assertFalse(is_institution_member(self.user, self.institution))

    def test_get_user_roles_returns_assigned_roles(self):
        membership = self._make_membership()
        MembershipRole.objects.create(membership=membership, role=self.role)

        self.assertQuerySetEqual(get_user_roles(self.user, self.institution), [self.role])

    def test_get_membership_access_bundles_roles_and_permissions(self):
        membership = self._make_membership()
        MembershipRole.objects.create(membership=membership, role=self.role)

        access = get_membership_access(self.user, self.institution)

        self.assertEqual(access.role_names, frozenset({"Teacher"}))
        self.assertEqual(access.permission_codes, frozenset({"attendance.record.create"}))

    def test_get_membership_access_is_empty_with_no_membership(self):
        access = get_membership_access(self.user, self.institution)

        self.assertEqual(access.role_names, frozenset())
        self.assertEqual(access.permission_codes, frozenset())

    def test_get_members_with_role_returns_users_holding_that_role(self):
        membership = self._make_membership()
        MembershipRole.objects.create(membership=membership, role=self.role)
        other_user = User.objects.create_user(email="other@stmary.ac.ke", password="x" * 12)
        InstitutionMembership.objects.create(user=other_user, institution=self.institution)

        self.assertEqual(list(get_members_with_role(self.institution, "Teacher")), [self.user])

    def test_get_members_with_role_excludes_suspended_memberships(self):
        membership = self._make_membership(status=InstitutionMembership.Status.SUSPENDED)
        MembershipRole.objects.create(membership=membership, role=self.role)

        self.assertEqual(list(get_members_with_role(self.institution, "Teacher")), [])

    def test_get_membership_access_is_cached(self):
        membership = self._make_membership()
        MembershipRole.objects.create(membership=membership, role=self.role)
        get_membership_access(self.user, self.institution)

        # Mutate the DB without going through services.assign_role (which
        # would invalidate the cache) — a cached call must not see this.
        MembershipRole.objects.filter(membership=membership, role=self.role).delete()

        access = get_membership_access(self.user, self.institution)
        self.assertEqual(access.role_names, frozenset({"Teacher"}))

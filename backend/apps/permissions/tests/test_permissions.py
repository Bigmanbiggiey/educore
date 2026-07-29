from types import SimpleNamespace

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
from apps.permissions.permissions import HasPermission, HasRole, IsInstitutionMember


def _request(*, user, institution):
    return SimpleNamespace(user=user, institution=institution)


class IsInstitutionMemberTests(TestCase):
    def setUp(self):
        cache.clear()
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.user = User.objects.create_user(email="teacher@stmary.ac.ke", password="x" * 12)
        self.permission_class = IsInstitutionMember()

    def test_denies_a_non_member(self):
        request = _request(user=self.user, institution=self.institution)
        self.assertFalse(self.permission_class.has_permission(request, None))

    def test_allows_an_active_member(self):
        InstitutionMembership.objects.create(user=self.user, institution=self.institution)
        request = _request(user=self.user, institution=self.institution)
        self.assertTrue(self.permission_class.has_permission(request, None))

    def test_denies_when_no_institution_is_bound(self):
        request = _request(user=self.user, institution=None)
        self.assertFalse(self.permission_class.has_permission(request, None))

    def test_denies_an_unauthenticated_user(self):
        anonymous = SimpleNamespace(is_authenticated=False)
        request = _request(user=anonymous, institution=self.institution)
        self.assertFalse(self.permission_class.has_permission(request, None))


class HasRoleTests(TestCase):
    def setUp(self):
        cache.clear()
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.user = User.objects.create_user(email="teacher@stmary.ac.ke", password="x" * 12)
        self.membership = InstitutionMembership.objects.create(
            user=self.user, institution=self.institution
        )
        # Institution-scoped, not a global template — sidesteps collision
        # with the 12 seeded system roles (migration 0002).
        self.teacher_role = Role.objects.create(name="Teacher", institution=self.institution)
        MembershipRole.objects.create(membership=self.membership, role=self.teacher_role)

    def test_allows_a_matching_role(self):
        permission_class = HasRole("Teacher")()
        request = _request(user=self.user, institution=self.institution)
        self.assertTrue(permission_class.has_permission(request, None))

    def test_allows_when_any_of_several_roles_match(self):
        permission_class = HasRole("Principal", "Teacher")()
        request = _request(user=self.user, institution=self.institution)
        self.assertTrue(permission_class.has_permission(request, None))

    def test_denies_a_non_matching_role(self):
        permission_class = HasRole("Principal")()
        request = _request(user=self.user, institution=self.institution)
        self.assertFalse(permission_class.has_permission(request, None))


class HasPermissionTests(TestCase):
    def setUp(self):
        cache.clear()
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.user = User.objects.create_user(email="teacher@stmary.ac.ke", password="x" * 12)
        membership = InstitutionMembership.objects.create(
            user=self.user, institution=self.institution
        )
        role = Role.objects.create(name="Teacher", institution=self.institution)
        permission = Permission.objects.create(code="attendance.record.create")
        RolePermission.objects.create(role=role, permission=permission)
        MembershipRole.objects.create(membership=membership, role=role)

    def test_allows_a_granted_permission_code(self):
        permission_class = HasPermission("attendance.record.create")()
        request = _request(user=self.user, institution=self.institution)
        self.assertTrue(permission_class.has_permission(request, None))

    def test_denies_an_ungranted_permission_code(self):
        permission_class = HasPermission("finance.invoice.create")()
        request = _request(user=self.user, institution=self.institution)
        self.assertFalse(permission_class.has_permission(request, None))

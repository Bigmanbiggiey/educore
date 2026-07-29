from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.accounts.models import User
from apps.institutions.models import Institution
from apps.permissions.models import InstitutionMembership, Permission, Role


class RoleConstraintTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")

    def test_two_global_roles_cannot_share_a_name(self):
        # A name not among the 12 seeded system roles (migration 0002) —
        # this test is about the constraint, not the seed data.
        Role.objects.create(name="Custom Global Role", institution=None)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Role.objects.create(name="Custom Global Role", institution=None)

    def test_two_institutions_can_each_have_a_role_with_the_same_name(self):
        other = Institution.objects.create(name="Kiambu High", slug="kiambu-high")
        Role.objects.create(name="Exams Coordinator", institution=self.institution)
        Role.objects.create(name="Exams Coordinator", institution=other)  # must not raise

    def test_one_institution_cannot_have_two_roles_with_the_same_name(self):
        Role.objects.create(name="Exams Coordinator", institution=self.institution)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Role.objects.create(name="Exams Coordinator", institution=self.institution)


class PermissionConstraintTests(TestCase):
    def test_code_must_be_unique(self):
        Permission.objects.create(code="finance.invoice.view")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Permission.objects.create(code="finance.invoice.view")

    def test_defaults_to_institution_scope(self):
        permission = Permission.objects.create(code="finance.invoice.view")
        self.assertEqual(permission.scope, Permission.Scope.INSTITUTION)


class InstitutionMembershipConstraintTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.user = User.objects.create_user(email="teacher@stmary.ac.ke", password="x" * 12)

    def test_one_membership_per_user_per_institution(self):
        InstitutionMembership.objects.create(user=self.user, institution=self.institution)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                InstitutionMembership.objects.create(user=self.user, institution=self.institution)

    def test_defaults_to_active_status(self):
        membership = InstitutionMembership.objects.create(
            user=self.user, institution=self.institution
        )
        self.assertEqual(membership.status, InstitutionMembership.Status.ACTIVE)

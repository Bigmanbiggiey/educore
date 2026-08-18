from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase

from apps.accounts.models import User
from apps.core.signals import audit_event, notification_requested
from apps.institutions.models import Institution
from apps.permissions.models import InstitutionMembership, MembershipRole, Permission, Role
from apps.permissions.selectors import get_membership_access
from apps.permissions.services import (
    assign_role,
    create_membership,
    grant_permission_to_role,
    invite_member,
    provision_institution_admin,
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


class ProvisionInstitutionAdminTests(TestCase):
    """`provision_institution_admin`'s own contract: it creates the User/
    Membership/Role/reset-token (all legally within reach: `permissions`
    imports both `accounts` and `institutions`), and it fires
    `audit_event`/`notification_requested` with the right payload — mocked
    here at the `apps.core.signals` boundary rather than importing
    `apps.audit`/`apps.notifications_core` to inspect real rows, since
    those are independent Layer 0 siblings this app can't import
    (`.importlinter`). What each signal's receiver actually does with that
    payload is `audit`'s/`notifications_core`'s own test suites' job.
    """

    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")

    @patch.object(notification_requested, "send")
    @patch.object(audit_event, "send")
    def test_creates_user_membership_and_role(self, mock_audit_send, mock_notification_send):
        platform_staff = User.objects.create_user(
            email="platform@educore.africa", password="x" * 12, is_platform_staff=True
        )

        membership = provision_institution_admin(
            institution=self.institution,
            admin_email="admin@stmary.ac.ke",
            actor=platform_staff,
        )

        admin_user = User.objects.get(email="admin@stmary.ac.ke")
        self.assertEqual(membership.user, admin_user)
        self.assertEqual(membership.institution, self.institution)
        self.assertTrue(membership.is_default)
        self.assertEqual(membership.status, InstitutionMembership.Status.ACTIVE)
        self.assertTrue(
            MembershipRole.objects.filter(
                membership=membership,
                role=Role.objects.get(name="Institution Administrator", institution__isnull=True),
            ).exists()
        )
        self.assertTrue(admin_user.password_reset_tokens.filter(used_at__isnull=True).exists())

        mock_audit_send.assert_called_once_with(
            sender=provision_institution_admin,
            actor=platform_staff,
            institution=self.institution,
            action="platform.institution.admin_provisioned",
            target=admin_user,
        )
        mock_notification_send.assert_called_once()
        notification_kwargs = mock_notification_send.call_args.kwargs
        self.assertEqual(notification_kwargs["institution"], self.institution)
        self.assertEqual(notification_kwargs["recipient"], admin_user)
        self.assertEqual(notification_kwargs["template_key"], "institution_admin_welcome")
        self.assertEqual(notification_kwargs["channel"], "email")
        self.assertIn("reset_url", notification_kwargs["context"])

    @patch.object(notification_requested, "send")
    @patch.object(audit_event, "send")
    def test_rejects_an_already_registered_admin_email(
        self, mock_audit_send, mock_notification_send
    ):
        User.objects.create_user(email="admin@stmary.ac.ke", password="x" * 12)

        with self.assertRaises(ValueError):
            provision_institution_admin(
                institution=self.institution, admin_email="admin@stmary.ac.ke"
            )

        mock_audit_send.assert_not_called()
        mock_notification_send.assert_not_called()


class InviteMemberTests(TestCase):
    """`invite_member`'s own contract — same mocked-signal-boundary
    reasoning as `ProvisionInstitutionAdminTests` above, since this
    function fires the exact same two signals."""

    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")

    @patch.object(notification_requested, "send")
    @patch.object(audit_event, "send")
    def test_creates_user_membership_and_role(self, mock_audit_send, mock_notification_send):
        admin = User.objects.create_user(email="admin@stmary.ac.ke", password="x" * 12)

        membership = invite_member(
            institution=self.institution,
            role_name="Teacher",
            email="teacher@stmary.ac.ke",
            actor=admin,
        )

        teacher_user = User.objects.get(email="teacher@stmary.ac.ke")
        self.assertEqual(membership.user, teacher_user)
        self.assertEqual(membership.institution, self.institution)
        self.assertTrue(membership.is_default)
        self.assertTrue(
            MembershipRole.objects.filter(
                membership=membership,
                role=Role.objects.get(name="Teacher", institution__isnull=True),
            ).exists()
        )
        self.assertTrue(teacher_user.password_reset_tokens.filter(used_at__isnull=True).exists())

        mock_audit_send.assert_called_once_with(
            sender=invite_member,
            actor=admin,
            institution=self.institution,
            action="permissions.membership.member_invited",
            target=teacher_user,
        )
        mock_notification_send.assert_called_once()
        notification_kwargs = mock_notification_send.call_args.kwargs
        self.assertEqual(notification_kwargs["institution"], self.institution)
        self.assertEqual(notification_kwargs["recipient"], teacher_user)
        self.assertEqual(notification_kwargs["template_key"], "member_welcome")
        self.assertEqual(notification_kwargs["channel"], "email")
        self.assertEqual(notification_kwargs["context"]["role_name"], "Teacher")
        self.assertIn("reset_url", notification_kwargs["context"])

    @patch.object(notification_requested, "send")
    @patch.object(audit_event, "send")
    def test_rejects_an_already_registered_email(self, mock_audit_send, mock_notification_send):
        User.objects.create_user(email="teacher@stmary.ac.ke", password="x" * 12)

        with self.assertRaises(ValueError):
            invite_member(
                institution=self.institution, role_name="Teacher", email="teacher@stmary.ac.ke"
            )

        mock_audit_send.assert_not_called()
        mock_notification_send.assert_not_called()

    @patch.object(notification_requested, "send")
    @patch.object(audit_event, "send")
    def test_rejects_a_non_invitable_role(self, mock_audit_send, mock_notification_send):
        for role_name in ("Institution Administrator", "System Administrator", "Made Up Role"):
            with self.assertRaises(ValueError):
                invite_member(
                    institution=self.institution, role_name=role_name, email="x@stmary.ac.ke"
                )

        self.assertFalse(User.objects.filter(email="x@stmary.ac.ke").exists())
        mock_audit_send.assert_not_called()
        mock_notification_send.assert_not_called()


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

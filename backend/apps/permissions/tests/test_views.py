from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.institutions.models import Domain, Institution
from apps.permissions.models import (
    InstitutionMembership,
    MembershipRole,
    Permission,
    Role,
    RolePermission,
)

HOSTNAME = "st-mary.educore.africa"
PLATFORM_HOST = "admin.educore.africa"
COOKIE_NAME = "refresh_token"

# Login/refresh/logout are all anonymous-by-design endpoints sharing one
# IP-keyed anon-throttle bucket (docs/api-design.md §13's 5/min default) —
# a single test class's setUp+several assertions easily exceeds that.
# Disabled here since throttling itself isn't what's under test (same
# pattern as apps.accounts.tests.test_views).
_THROTTLING_DISABLED = {**settings.REST_FRAMEWORK, "DEFAULT_THROTTLE_CLASSES": []}


@override_settings(REST_FRAMEWORK=_THROTTLING_DISABLED)
class AuthViewTestCase(APITestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        Domain.objects.create(
            institution=self.institution,
            hostname=HOSTNAME,
            domain_type=Domain.DomainType.SUBDOMAIN,
            is_primary=True,
        )
        self.user = User.objects.create_user(
            email="teacher@stmary.ac.ke", password="a-decent-password"
        )
        self.membership = InstitutionMembership.objects.create(
            user=self.user, institution=self.institution
        )


class LoginViewTests(AuthViewTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:permissions:login")

    def test_successful_login_returns_an_access_token_and_sets_the_refresh_cookie(self):
        response = self.client.post(
            self.url,
            {"email_or_phone": "teacher@stmary.ac.ke", "password": "a-decent-password"},
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.data)
        cookie = response.cookies[COOKIE_NAME]
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["samesite"], "Strict")

    def test_wrong_password_is_unauthenticated(self):
        response = self.client.post(
            self.url,
            {"email_or_phone": "teacher@stmary.ac.ke", "password": "wrong-password"},
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["error"]["code"], "unauthenticated")

    def test_unknown_identifier_is_unauthenticated(self):
        response = self.client.post(
            self.url,
            {"email_or_phone": "nobody@nowhere.com", "password": "a-decent-password"},
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 401)

    def test_no_membership_at_this_institution_is_unauthenticated(self):
        User.objects.create_user(email="outsider@nowhere.com", password="a-decent-password")

        response = self.client.post(
            self.url,
            {"email_or_phone": "outsider@nowhere.com", "password": "a-decent-password"},
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 401)

    def test_suspended_membership_is_unauthenticated(self):
        self.membership.status = InstitutionMembership.Status.SUSPENDED
        self.membership.save(update_fields=["status"])

        response = self.client.post(
            self.url,
            {"email_or_phone": "teacher@stmary.ac.ke", "password": "a-decent-password"},
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 401)

    def test_login_on_a_platform_host_is_a_validation_error(self):
        # No HTTP_HOST override — the test client's default host
        # ("testserver") is a dev.py PLATFORM_HOST, so request.institution
        # is None here, same as any unresolved-tenant platform request.
        response = self.client.post(
            self.url,
            {"email_or_phone": "teacher@stmary.ac.ke", "password": "a-decent-password"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"]["code"], "validation_error")


class RefreshViewTests(AuthViewTestCase):
    def setUp(self):
        super().setUp()
        self.login_url = reverse("v1:permissions:login")
        self.refresh_url = reverse("v1:permissions:refresh")
        self.client.post(
            self.login_url,
            {"email_or_phone": "teacher@stmary.ac.ke", "password": "a-decent-password"},
            HTTP_HOST=HOSTNAME,
        )

    def test_valid_cookie_returns_a_new_access_token_and_rotates_the_cookie(self):
        original_refresh = self.client.cookies[COOKIE_NAME].value

        response = self.client.post(self.refresh_url, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.data)
        self.assertNotEqual(self.client.cookies[COOKIE_NAME].value, original_refresh)

    def test_the_old_refresh_token_is_blacklisted_after_rotation(self):
        original_refresh = self.client.cookies[COOKIE_NAME].value
        self.client.post(self.refresh_url, HTTP_HOST=HOSTNAME)  # rotates once

        self.client.cookies[COOKIE_NAME] = original_refresh
        response = self.client.post(self.refresh_url, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 401)

    def test_missing_cookie_is_unauthenticated(self):
        self.client.cookies.clear()

        response = self.client.post(self.refresh_url, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 401)

    def test_garbage_cookie_is_unauthenticated(self):
        self.client.cookies[COOKIE_NAME] = "not-a-real-token"

        response = self.client.post(self.refresh_url, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 401)


class LogoutViewTests(AuthViewTestCase):
    def setUp(self):
        super().setUp()
        self.client.post(
            reverse("v1:permissions:login"),
            {"email_or_phone": "teacher@stmary.ac.ke", "password": "a-decent-password"},
            HTTP_HOST=HOSTNAME,
        )
        self.logout_url = reverse("v1:permissions:logout")
        self.refresh_url = reverse("v1:permissions:refresh")

    def test_logout_blacklists_the_refresh_token_and_clears_the_cookie(self):
        refresh_value = self.client.cookies[COOKIE_NAME].value

        response = self.client.post(self.logout_url, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.cookies[COOKIE_NAME].value, "")

        self.client.cookies[COOKIE_NAME] = refresh_value
        refresh_response = self.client.post(self.refresh_url, HTTP_HOST=HOSTNAME)
        self.assertEqual(refresh_response.status_code, 401)

    def test_logout_without_a_cookie_is_idempotent(self):
        self.client.cookies.clear()

        response = self.client.post(self.logout_url, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 200)


class MeViewTests(AuthViewTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:permissions:me")

    def _bearer(self, user):
        return f"Bearer {RefreshToken.for_user(user).access_token}"

    def test_requires_authentication(self):
        response = self.client.get(self.url, HTTP_HOST=HOSTNAME)
        self.assertEqual(response.status_code, 401)

    def test_returns_the_user_and_roles_at_the_current_institution(self):
        role = Role.objects.create(name="Class Teacher", institution=self.institution)
        MembershipRole.objects.create(membership=self.membership, role=role)

        response = self.client.get(
            self.url, HTTP_HOST=HOSTNAME, HTTP_AUTHORIZATION=self._bearer(self.user)
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], "teacher@stmary.ac.ke")
        self.assertEqual(response.data["institution_membership"]["roles"], ["Class Teacher"])

    def test_institution_membership_is_null_without_an_active_membership(self):
        # A valid access token issued directly (bypassing login), for a user
        # with no membership here — simulates a membership revoked mid-session
        # (docs/permissions.md §6): the token is still valid, but access isn't.
        outsider = User.objects.create_user(
            email="outsider@nowhere.com", password="a-decent-password"
        )

        response = self.client.get(
            self.url, HTTP_HOST=HOSTNAME, HTTP_AUTHORIZATION=self._bearer(outsider)
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["institution_membership"])

    def test_platform_staff_on_the_platform_host_has_no_institution_membership(self):
        # request.institution is never set by TenantMiddleware on a
        # platform host without an active act-as session — this must not
        # 500 (AttributeError), it must report None like any other
        # no-membership-here state.
        platform_staff = User.objects.create_user(
            email="admin@educore.africa", password="a-decent-password", is_platform_staff=True
        )

        response = self.client.get(
            self.url, HTTP_HOST=PLATFORM_HOST, HTTP_AUTHORIZATION=self._bearer(platform_staff)
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["institution_membership"])


class InviteMemberViewTests(AuthViewTestCase):
    """Same fixture shape as `students.tests.test_views` uses for its
    `HasPermission`-gated endpoints: a role created ad hoc per test,
    carrying only the permission code(s) that test needs, rather than
    relying on the real seeded `Institution Administrator` role+grants
    (migration 0003) so this suite stays independent of that migration's
    exact contents."""

    def setUp(self):
        super().setUp()
        self.url = reverse("v1:permissions-members:member-invite")

    def _bearer(self, user):
        return f"Bearer {RefreshToken.for_user(user).access_token}"

    def _grant(self, *, permission_code):
        role = Role.objects.create(name="Registrar", institution=self.institution)
        permission = Permission.objects.create(code=permission_code)
        RolePermission.objects.create(role=role, permission=permission)
        MembershipRole.objects.create(membership=self.membership, role=role)

    def test_without_the_permission_is_denied(self):
        response = self.client.post(
            self.url,
            {"email": "new-teacher@stmary.ac.ke", "role_name": "Teacher"},
            HTTP_HOST=HOSTNAME,
            HTTP_AUTHORIZATION=self._bearer(self.user),
        )

        self.assertEqual(response.status_code, 403)

    def test_invites_a_member(self):
        self._grant(permission_code="permissions.membership.invite")

        response = self.client.post(
            self.url,
            {"email": "new-teacher@stmary.ac.ke", "role_name": "Teacher"},
            HTTP_HOST=HOSTNAME,
            HTTP_AUTHORIZATION=self._bearer(self.user),
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["email"], "new-teacher@stmary.ac.ke")
        self.assertEqual(response.data["role_name"], "Teacher")
        self.assertTrue(User.objects.filter(email="new-teacher@stmary.ac.ke").exists())

    def test_duplicate_email_is_a_validation_error(self):
        self._grant(permission_code="permissions.membership.invite")
        User.objects.create_user(email="new-teacher@stmary.ac.ke", password="x" * 12)

        response = self.client.post(
            self.url,
            {"email": "new-teacher@stmary.ac.ke", "role_name": "Teacher"},
            HTTP_HOST=HOSTNAME,
            HTTP_AUTHORIZATION=self._bearer(self.user),
        )

        self.assertEqual(response.status_code, 400)

from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.accounts.models import PasswordResetToken, User

# These endpoints are anonymous by design, so every test in this module
# shares one IP-keyed anon-throttle bucket (docs/api-design.md §13's
# 5/min default) — disable it here since throttling itself isn't what's
# under test. DRF only reloads its cached settings on changes to the
# `REST_FRAMEWORK` key itself, so the whole dict is overridden rather than
# just `DEFAULT_THROTTLE_CLASSES`.
_THROTTLING_DISABLED = {**settings.REST_FRAMEWORK, "DEFAULT_THROTTLE_CLASSES": []}


@override_settings(REST_FRAMEWORK=_THROTTLING_DISABLED)
class PasswordResetRequestViewTests(APITestCase):
    def setUp(self):
        self.url = reverse("v1:accounts:password-reset-request")

    def test_known_identifier_issues_a_token(self):
        user = User.objects.create_user(email="teacher@stmary.ac.ke", password="x" * 12)

        response = self.client.post(self.url, {"email_or_phone": "teacher@stmary.ac.ke"})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(PasswordResetToken.objects.filter(user=user).exists())

    def test_unknown_identifier_returns_the_same_generic_response(self):
        response = self.client.post(self.url, {"email_or_phone": "nobody@nowhere.com"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data, {"detail": "If an account exists, a reset link has been sent."}
        )

    def test_missing_identifier_is_a_validation_error(self):
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"]["code"], "validation_error")


@override_settings(REST_FRAMEWORK=_THROTTLING_DISABLED)
class PasswordResetConfirmViewTests(APITestCase):
    def setUp(self):
        self.url = reverse("v1:accounts:password-reset-confirm")
        self.user = User.objects.create_user(email="teacher@stmary.ac.ke", password="x" * 12)
        self.token = PasswordResetToken.objects.create(
            user=self.user,
            token="a-test-token",
            expires_at=self._an_hour_from_now(),
        )

    @staticmethod
    def _an_hour_from_now():
        from django.utils import timezone

        return timezone.now() + timezone.timedelta(hours=1)

    def test_valid_token_resets_the_password(self):
        response = self.client.post(
            self.url, {"token": "a-test-token", "new_password": "a-new-decent-password"}
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("a-new-decent-password"))

    def test_unknown_token_is_a_validation_error(self):
        response = self.client.post(
            self.url, {"token": "not-a-real-token", "new_password": "a-new-decent-password"}
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"]["code"], "validation_error")

    def test_weak_password_is_a_validation_error(self):
        response = self.client.post(self.url, {"token": "a-test-token", "new_password": "short"})

        self.assertEqual(response.status_code, 400)
        self.assertIn("new_password", response.data["error"]["fields"])

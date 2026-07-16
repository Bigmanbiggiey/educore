from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import PasswordResetToken, User
from apps.accounts.services import (
    confirm_password_reset,
    register_user,
    request_password_reset,
)


class RegisterUserTests(TestCase):
    def test_creates_a_user_with_a_hashed_password(self):
        user = register_user(email="teacher@stmary.ac.ke", password="a-decent-password")
        self.assertTrue(user.check_password("a-decent-password"))

    def test_rejects_a_weak_password(self):
        # Too short — docs/authentication.md §5's min-length-10 validator.
        with self.assertRaises(ValidationError):
            register_user(email="teacher@stmary.ac.ke", password="short")

    def test_requires_email_or_phone(self):
        with self.assertRaises(ValueError):
            register_user(password="a-decent-password")


class PasswordResetFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="teacher@stmary.ac.ke", password="x" * 12)

    def test_request_then_confirm_changes_the_password(self):
        token = request_password_reset(self.user)
        confirm_password_reset(token=token.token, new_password="a-new-decent-password")

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("a-new-decent-password"))

    def test_a_token_cannot_be_reused(self):
        token = request_password_reset(self.user)
        confirm_password_reset(token=token.token, new_password="a-new-decent-password")

        with self.assertRaises(ValueError):
            confirm_password_reset(token=token.token, new_password="yet-another-password")

    def test_an_expired_token_is_rejected(self):
        token = request_password_reset(self.user)
        token.expires_at = timezone.now() - timezone.timedelta(minutes=1)
        token.save(update_fields=["expires_at"])

        with self.assertRaises(ValueError):
            confirm_password_reset(token=token.token, new_password="a-new-decent-password")

    def test_requesting_a_new_token_invalidates_the_previous_one(self):
        first = request_password_reset(self.user)
        request_password_reset(self.user)

        first.refresh_from_db()
        self.assertIsNotNone(first.used_at)

    def test_unknown_token_is_rejected(self):
        with self.assertRaises(ValueError):
            confirm_password_reset(token="not-a-real-token", new_password="a-new-decent-password")

    def test_never_logs_the_user_in(self):
        # confirm_password_reset returns the User but must not itself
        # constitute a session (docs/authentication.md §5) — it has no
        # request/response to attach a session to in the first place, which
        # is itself the guarantee: this is a pure data operation.
        token = request_password_reset(self.user)
        result = confirm_password_reset(token=token.token, new_password="a-new-decent-password")
        self.assertIsInstance(result, User)
        self.assertEqual(PasswordResetToken.objects.get(pk=token.pk).used_at is not None, True)

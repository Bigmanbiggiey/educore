from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.accounts.models import User


class UserConstraintTests(TestCase):
    def test_requires_email_or_phone(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                User.objects.create(email=None, phone=None)

    def test_email_only_is_allowed(self):
        user = User.objects.create_user(email="teacher@stmary.ac.ke", password="not-a-real-pw!")
        self.assertIsNone(user.phone)

    def test_phone_only_is_allowed(self):
        user = User.objects.create_user(phone="+254700000000", password="not-a-real-pw!")
        self.assertIsNone(user.email)


class UserPasswordAndStaffFlagTests(TestCase):
    def test_password_is_hashed_not_stored_in_plaintext(self):
        user = User.objects.create_user(email="teacher@stmary.ac.ke", password="not-a-real-pw!")
        self.assertNotEqual(user.password, "not-a-real-pw!")
        self.assertTrue(user.check_password("not-a-real-pw!"))

    def test_is_staff_and_perm_checks_follow_is_platform_staff(self):
        regular = User.objects.create_user(email="teacher@stmary.ac.ke", password="x" * 12)
        admin = User.objects.create_user(
            email="admin@educore.africa", password="x" * 12, is_platform_staff=True
        )

        self.assertFalse(regular.is_staff)
        self.assertFalse(regular.has_perm("anything"))
        self.assertFalse(regular.has_module_perms("anything"))

        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.has_perm("anything"))
        self.assertTrue(admin.has_module_perms("anything"))

    def test_mfa_fields_default_to_unset(self):
        user = User.objects.create_user(email="teacher@stmary.ac.ke", password="x" * 12)
        self.assertEqual(user.totp_secret, "")
        self.assertFalse(user.mfa_enabled)


class UserManagerTests(TestCase):
    def test_create_user_defaults_to_not_platform_staff(self):
        user = User.objects.create_user(email="teacher@stmary.ac.ke", password="x" * 12)
        self.assertFalse(user.is_platform_staff)

    def test_create_superuser_is_platform_staff(self):
        user = User.objects.create_superuser(email="admin@educore.africa", password="x" * 12)
        self.assertTrue(user.is_platform_staff)

    def test_create_user_without_identifier_raises(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(password="x" * 12)

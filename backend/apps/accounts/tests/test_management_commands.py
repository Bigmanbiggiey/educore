from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from apps.accounts.models import User


class BootstrapPlatformAdminTests(TestCase):
    def test_creates_a_platform_staff_user(self):
        out = StringIO()
        call_command(
            "bootstrap_platform_admin",
            "--email=admin@educore.africa",
            "--password=a-decent-bootstrap-password",
            stdout=out,
        )

        user = User.objects.get(email="admin@educore.africa")
        self.assertTrue(user.is_platform_staff)
        self.assertTrue(user.check_password("a-decent-bootstrap-password"))

    def test_refuses_when_a_platform_admin_already_exists(self):
        User.objects.create_user(
            email="existing@educore.africa", password="x" * 12, is_platform_staff=True
        )

        with self.assertRaises(CommandError):
            call_command(
                "bootstrap_platform_admin",
                "--email=admin@educore.africa",
                "--password=a-decent-bootstrap-password",
            )
        self.assertFalse(User.objects.filter(email="admin@educore.africa").exists())

    def test_requires_email_or_phone(self):
        with self.assertRaises(CommandError):
            call_command("bootstrap_platform_admin", "--password=a-decent-bootstrap-password")

    def test_requires_a_password(self):
        with self.assertRaises(CommandError):
            call_command("bootstrap_platform_admin", "--email=admin@educore.africa")

    def test_rejects_a_weak_password(self):
        with self.assertRaises(CommandError):
            call_command(
                "bootstrap_platform_admin", "--email=admin@educore.africa", "--password=short"
            )

    @patch.dict(
        "os.environ",
        {
            "PLATFORM_ADMIN_EMAIL": "env-admin@educore.africa",
            "PLATFORM_ADMIN_PASSWORD": "a-decent-bootstrap-password",
        },
    )
    def test_reads_from_environment_variables(self):
        call_command("bootstrap_platform_admin")

        self.assertTrue(
            User.objects.filter(
                email="env-admin@educore.africa", is_platform_staff=True
            ).exists()
        )

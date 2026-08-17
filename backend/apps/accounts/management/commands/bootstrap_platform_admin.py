"""Bootstraps the very first platform System Administrator on a fresh
install (empty `User` table) — docs/deployment.md's First-Run Bootstrap
step. Deliberately a manual, one-time command, not wired into
entrypoint.sh — a fresh environment gets exactly one platform admin,
created once, by whoever holds the deploy secrets.
"""

import os

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import User
from apps.accounts.services import register_user


class Command(BaseCommand):
    help = "Creates the first platform System Administrator (is_platform_staff=True)."

    def add_arguments(self, parser):
        parser.add_argument("--email", default=None)
        parser.add_argument("--phone", default=None)
        parser.add_argument("--password", default=None)

    def handle(self, *args, **options):
        if User.objects.filter(is_platform_staff=True).exists():
            raise CommandError(
                "A platform System Administrator already exists — refusing to create "
                "another. Manage existing platform staff via Django admin or the shell."
            )

        email = options["email"] or os.environ.get("PLATFORM_ADMIN_EMAIL")
        phone = options["phone"] or os.environ.get("PLATFORM_ADMIN_PHONE")
        password = options["password"] or os.environ.get("PLATFORM_ADMIN_PASSWORD")

        if not email and not phone:
            raise CommandError(
                "Provide --email/--phone or set PLATFORM_ADMIN_EMAIL/PLATFORM_ADMIN_PHONE."
            )
        if not password:
            raise CommandError("Provide --password or set PLATFORM_ADMIN_PASSWORD.")

        try:
            user = register_user(email=email, phone=phone, password=password)
        except (ValueError, ValidationError) as exc:
            raise CommandError(str(exc)) from exc

        user.is_platform_staff = True
        user.save(update_fields=["is_platform_staff"])

        self.stdout.write(self.style.SUCCESS(f"Created platform System Administrator: {user}"))

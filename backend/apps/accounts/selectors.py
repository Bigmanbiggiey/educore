"""Public read interface for `accounts` — docs/modules.md."""

from django.db import models

from apps.accounts.models import User


def get_user_by_email(email: str) -> User | None:
    return User.objects.filter(email__iexact=email).first()


def get_user_by_phone(phone: str) -> User | None:
    return User.objects.filter(phone=phone).first()


def get_user_by_email_or_phone(identifier: str) -> User | None:
    """Login accepts either identifier (docs/authentication.md §3) without
    the caller needing to know up front which kind it is."""
    return User.objects.filter(
        models.Q(email__iexact=identifier) | models.Q(phone=identifier)
    ).first()

"""Public write interface for `accounts` — docs/modules.md. Other apps
mutate account state only through these functions, never by touching
apps.accounts.models directly (docs/project-structure.md §3).
"""

import secrets
from datetime import timedelta

from django.contrib.auth.password_validation import validate_password
from django.utils import timezone

from apps.accounts.models import PasswordResetToken, User

PASSWORD_RESET_TOKEN_LIFETIME = timedelta(hours=1)


def register_user(*, email: str | None = None, phone: str | None = None, password: str) -> User:
    """Creates a new User with a validated password (docs/authentication.md
    §5: Django's minimum-length/common-password/similarity/numeric validators).
    """
    if not email and not phone:
        raise ValueError("A user requires an email or a phone number")
    user = User(email=email, phone=phone)
    validate_password(password, user=user)
    user.set_password(password)
    user.save()
    return user


def request_password_reset(user: User) -> PasswordResetToken:
    """Issues a single-use, 1-hour token (docs/authentication.md §5).

    Delivering it (email or SMS, per the user's notification preference) is
    `notifications_core.services.send(...)`'s job once that app exists —
    this only issues and invalidates tokens.
    """
    PasswordResetToken.objects.filter(user=user, used_at__isnull=True).update(
        used_at=timezone.now()
    )
    return PasswordResetToken.objects.create(
        user=user,
        token=secrets.token_urlsafe(32),
        expires_at=timezone.now() + PASSWORD_RESET_TOKEN_LIFETIME,
    )


def confirm_password_reset(*, token: str, new_password: str) -> User:
    """Consumes a password reset token and sets a new password.

    Never logs the user in directly (docs/authentication.md §5) — the
    caller still goes through the normal login flow afterward.
    """
    try:
        reset_token = PasswordResetToken.objects.select_related("user").get(token=token)
    except PasswordResetToken.DoesNotExist:
        raise ValueError("Invalid or unknown reset token") from None

    if reset_token.used_at is not None:
        raise ValueError("This reset token has already been used")
    if reset_token.expires_at < timezone.now():
        raise ValueError("This reset token has expired")

    user = reset_token.user
    validate_password(new_password, user=user)
    user.set_password(new_password)
    user.save(update_fields=["password"])

    reset_token.used_at = timezone.now()
    reset_token.save(update_fields=["used_at"])
    return user

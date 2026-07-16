"""Layer 0 identity model — docs/database.md §2, docs/modules.md
(`accounts`). Identity only: no role, no institution membership, no
profile fields (name, etc.) — those live on `permissions.InstitutionMembership`
and the relevant Layer 1 profile models (`StaffProfile`, `ParentProfile`,
`Student`) respectively, since a user can hold different roles at different
institutions (docs/modules.md's own rationale for this split).
"""

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models

from apps.core.models import TimeStampedModel, UUIDPrimaryKeyModel


class UserManager(BaseUserManager):
    def _create_user(self, email=None, phone=None, password=None, **extra_fields):
        if not email and not phone:
            raise ValueError("A user requires an email or a phone number")
        if email:
            email = self.normalize_email(email)
        user = self.model(email=email, phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, phone=None, password=None, **extra_fields):
        extra_fields.setdefault("is_platform_staff", False)
        return self._create_user(email=email, phone=phone, password=password, **extra_fields)

    def create_superuser(self, email=None, phone=None, password=None, **extra_fields):
        extra_fields["is_platform_staff"] = True
        return self._create_user(email=email, phone=phone, password=password, **extra_fields)


class User(UUIDPrimaryKeyModel, AbstractBaseUser):
    email = models.EmailField(unique=True, null=True, blank=True)
    # E.164 format, validated at the serializer layer once the registration
    # API exists — not enforced by a DB regex here.
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)

    # System Administrator portal access (docs/database.md §2) — replaces
    # Django's is_superuser/is_staff, since RBAC here is the fully custom
    # Role/Permission system in `permissions`, not Django's built-in one
    # (see has_perm/has_module_perms below).
    is_platform_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    # MFA fields reserved now, enforcement built later (docs/authentication.md
    # §5): cheaper to add this column while the table holds no live data than
    # to retrofit it onto the platform's most sensitive table later. Empty
    # string rather than null, per the same CharField convention used
    # elsewhere (e.g. Institution.db_alias) despite database.md calling
    # totp_secret "nullable" — empty string serves the same "unset" intent.
    totp_secret = models.CharField(max_length=64, blank=True, default="")
    mfa_enabled = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(email__isnull=False) | models.Q(phone__isnull=False),
                name="user_requires_email_or_phone",
            )
        ]

    def __str__(self) -> str:
        return self.email or self.phone or str(self.id)

    @property
    def is_staff(self) -> bool:
        """Gates Django admin site access. Reuses is_platform_staff rather
        than adding a second, undocumented staff flag — docs/database.md
        §2 only specifies is_platform_staff."""
        return self.is_platform_staff

    def has_perm(self, perm, obj=None) -> bool:
        return self.is_platform_staff

    def has_module_perms(self, app_label) -> bool:
        return self.is_platform_staff


class PasswordResetToken(TimeStampedModel):
    """Not itemized in docs/database.md's User table, but required to
    implement the single-use, 1-hour reset token docs/authentication.md §5
    describes. Delivering the token (email/SMS) is `notifications_core`'s
    job once that app exists — this only issues and validates it.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_reset_tokens")
    token = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Password reset for {self.user}"

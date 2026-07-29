"""Request/response shapes for `accounts`'s auth-adjacent endpoints —
docs/api-design.md §7. Login/refresh/logout/me are not implemented here:
docs/authentication.md §3 requires an active `InstitutionMembership` check
that `permissions` (not yet built) owns.
"""

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.accounts.services import confirm_password_reset


class PasswordResetRequestSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

    def save(self):
        try:
            return confirm_password_reset(
                token=self.validated_data["token"],
                new_password=self.validated_data["new_password"],
            )
        except ValueError as exc:
            raise serializers.ValidationError({"token": [str(exc)]}) from None
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"new_password": exc.messages}) from None

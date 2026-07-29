"""Auth-adjacent endpoints `accounts` owns — docs/api-design.md §7:
password reset request/confirm. Unauthenticated by nature; rate-limited by
the project-wide `AnonRateThrottle` (docs/api-design.md §13).
"""

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.selectors import get_user_by_email_or_phone
from apps.accounts.serializers import (
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
)
from apps.accounts.services import request_password_reset

# Generic response body regardless of whether the identifier matched a user
# — confirming/denying account existence here is a user-enumeration leak.
_GENERIC_ACK = {"detail": "If an account exists, a reset link has been sent."}


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=PasswordResetRequestSerializer, responses={200: None})
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = get_user_by_email_or_phone(serializer.validated_data["email_or_phone"])
        if user is not None:
            # Delivery (email/SMS) lands once `notifications_core` exists
            # (docs/authentication.md §5) — this only issues the token.
            request_password_reset(user)

        return Response(_GENERIC_ACK)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=PasswordResetConfirmSerializer, responses={200: None})
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password has been reset."})

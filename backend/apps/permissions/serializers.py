"""Request/response shapes for the login/refresh/logout/me endpoints
`permissions` owns — docs/api-design.md §7. These live here, not in
`accounts`, because docs/authentication.md §3 requires an active
`InstitutionMembership` check on login that `accounts` alone can't do
(`accounts` doesn't depend on `permissions` — the reverse does).
"""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

from apps.accounts.selectors import get_user_by_email_or_phone
from apps.permissions.selectors import get_membership_access, is_institution_member


class LoginSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        request = self.context["request"]
        institution = getattr(request, "institution", None)
        if institution is None:
            raise serializers.ValidationError(
                "Login requires an institution-specific host, not a platform host."
            )

        user = get_user_by_email_or_phone(attrs["email_or_phone"])
        if user is None or not user.is_active or not user.check_password(attrs["password"]):
            raise AuthenticationFailed("No active account found with the given credentials.")

        # A valid password with no active membership at *this* hostname
        # fails login here, not later at the first protected endpoint
        # (docs/authentication.md §3).
        if not is_institution_member(user, institution):
            raise AuthenticationFailed("No active membership at this institution.")

        attrs["user"] = user
        attrs["institution"] = institution
        return attrs


class PlatformLoginSerializer(serializers.Serializer):
    """Parallel to `LoginSerializer`, not a branch inside it — deliberately
    never reads `request.institution` (docs/permissions.md §7: platform
    staff access has nothing to do with institution membership)."""

    email_or_phone = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = get_user_by_email_or_phone(attrs["email_or_phone"])
        if user is None or not user.is_active or not user.check_password(attrs["password"]):
            raise AuthenticationFailed("No active account found with the given credentials.")
        if not user.is_platform_staff:
            raise AuthenticationFailed("No active account found with the given credentials.")

        attrs["user"] = user
        return attrs


class InstitutionMembershipSummarySerializer(serializers.Serializer):
    roles = serializers.ListField(child=serializers.CharField())


class MeSerializer(serializers.Serializer):
    """`institution_membership` is null when the authenticated user has no
    active membership at the current request's institution — a session can
    outlive a revoked membership until its 15-minute access token expires
    (docs/permissions.md §6), and this endpoint reports that state rather
    than erroring."""

    id = serializers.UUIDField()
    email = serializers.EmailField(allow_null=True)
    phone = serializers.CharField(allow_null=True)
    is_platform_staff = serializers.BooleanField()
    institution_membership = serializers.SerializerMethodField()

    @extend_schema_field(InstitutionMembershipSummarySerializer(allow_null=True))
    def get_institution_membership(self, user):
        # Never set by TenantMiddleware on a platform host unless an
        # act-as session is active (apps/institutions/middleware.py) — a
        # platform-staff user calling /me/ with no such session has no
        # `request.institution` at all, not an institution they're simply
        # not a member of.
        institution = getattr(self.context["request"], "institution", None)
        if institution is None or not is_institution_member(user, institution):
            return None
        access = get_membership_access(user, institution)
        return {"roles": sorted(access.role_names)}

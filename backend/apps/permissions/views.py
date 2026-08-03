"""Login/refresh/logout/me — docs/api-design.md §7, docs/authentication.md
§1-4. The refresh token is never in a JSON body, only an httpOnly/Secure/
SameSite=Strict cookie the frontend never touches directly
(docs/frontend-architecture.md §2) — these views are the only code that
reads or writes that cookie.
"""

import time
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from apps.core.permissions import IsPlatformStaff
from apps.core.signals import audit_event
from apps.institutions.models import Institution
from apps.permissions.serializers import LoginSerializer, MeSerializer, PlatformLoginSerializer

ACT_AS_TOKEN_LIFETIME = timedelta(minutes=30)


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        settings.REFRESH_TOKEN_COOKIE_NAME,
        token,
        max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
        path=settings.REFRESH_TOKEN_COOKIE_PATH,
        secure=settings.REFRESH_TOKEN_COOKIE_SECURE,
        httponly=True,
        samesite="Strict",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        settings.REFRESH_TOKEN_COOKIE_NAME, path=settings.REFRESH_TOKEN_COOKIE_PATH
    )


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=LoginSerializer, responses={200: None})
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)
        response = Response({"access_token": str(refresh.access_token)})
        _set_refresh_cookie(response, str(refresh))
        return response


class HostContextView(APIView):
    """Tells the frontend which login flow to render — `docs/permissions.md`
    §7's platform-staff login only makes sense on a platform host.
    `TenantMiddleware` has already 404'd any genuinely-unresolvable host by
    the time this runs, so `request.institution is None` here can only mean
    "platform host", never "unknown host".
    """

    permission_classes = [AllowAny]

    @extend_schema(request=None, responses={200: None})
    def get(self, request):
        host_type = "institution" if getattr(request, "institution", None) else "platform"
        return Response({"host_type": host_type})


class PlatformLoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=PlatformLoginSerializer, responses={200: None})
    def post(self, request):
        serializer = PlatformLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)
        response = Response({"access_token": str(refresh.access_token)})
        _set_refresh_cookie(response, str(refresh))
        return response


class ActAsView(APIView):
    """Starts a break-glass session (docs/permissions.md §7) — mints a
    short-lived, elevated access token scoped to one institution, rather
    than a new login. Audited as `platform.admin.impersonate_start`.
    """

    permission_classes = [IsPlatformStaff]

    @extend_schema(request=None, responses={200: None})
    def post(self, request, institution_id=None):
        institution = get_object_or_404(Institution, id=institution_id, is_active=True)

        token = AccessToken.for_user(request.user)
        token.set_exp(lifetime=ACT_AS_TOKEN_LIFETIME)
        token["acting_as_admin"] = True
        token["acting_institution_id"] = str(institution.id)

        audit_event.send(
            sender=self.__class__,
            actor=request.user,
            institution=institution,
            action="platform.admin.impersonate_start",
            acting_as_admin=True,
        )
        return Response({"access_token": str(token)})


class EndActAsView(APIView):
    """Ends a break-glass session on explicit exit (docs/permissions.md
    §7) — revokes the elevated token immediately (rather than relying on
    its natural 30-minute expiry) by flagging its `jti` in the cache,
    which `TenantMiddleware._resolve_acting_institution` checks on every
    subsequent request. Audited as `platform.admin.impersonate_end`.
    """

    permission_classes = [IsPlatformStaff]

    @extend_schema(request=None, responses={200: None})
    def post(self, request):
        token = request.auth
        institution_id = token.get("acting_institution_id") if token else None
        institution = (
            Institution.objects.filter(id=institution_id).first() if institution_id else None
        )

        if token is not None:
            jti = token.get("jti")
            remaining = int(token["exp"] - time.time())
            if jti and remaining > 0:
                cache.set(f"impersonation_revoked:{jti}", True, timeout=remaining)

        audit_event.send(
            sender=self.__class__,
            actor=request.user,
            institution=institution,
            action="platform.admin.impersonate_end",
            acting_as_admin=True,
        )
        return Response({"detail": "Break-glass session ended."})


class RefreshView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=None, responses={200: None})
    def post(self, request):
        raw_refresh = request.COOKIES.get(settings.REFRESH_TOKEN_COOKIE_NAME)
        if not raw_refresh:
            raise AuthenticationFailed("No refresh token cookie present.")

        serializer = TokenRefreshSerializer(data={"refresh": raw_refresh})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as exc:
            # Re-raised as a plain AuthenticationFailed, not simplejwt's own
            # InvalidToken — InvalidToken's `detail` is a nested dict
            # ({"detail": ..., "code": ...}), which api.exception_handlers's
            # single-`detail`-key check would stringify as a raw dict repr
            # instead of a clean message.
            raise AuthenticationFailed(str(exc)) from exc

        response = Response({"access_token": serializer.validated_data["access"]})
        rotated_refresh = serializer.validated_data.get("refresh")
        if rotated_refresh:
            _set_refresh_cookie(response, rotated_refresh)
        return response


class LogoutView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=None, responses={200: None})
    def post(self, request):
        raw_refresh = request.COOKIES.get(settings.REFRESH_TOKEN_COOKIE_NAME)
        if raw_refresh:
            try:
                RefreshToken(raw_refresh).blacklist()
            except TokenError:
                # Already invalid/expired/blacklisted — logout is
                # idempotent either way, so this isn't itself an error.
                pass

        response = Response({"detail": "Logged out."})
        _clear_refresh_cookie(response)
        return response


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: MeSerializer})
    def get(self, request):
        serializer = MeSerializer(request.user, context={"request": request})
        return Response(serializer.data)

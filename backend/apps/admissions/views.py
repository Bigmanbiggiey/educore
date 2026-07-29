"""API views for `admissions` — docs/api-design.md, docs/authentication.md §6.
`POST /api/v1/applications/` is one of the few genuinely public,
unauthenticated write endpoints — a prospective parent has no account yet —
still tenant-resolved via the `Host` header (`TenantMiddleware` runs before
authentication), relying on the project-wide default `AnonRateThrottle`,
same pattern as `accounts`'s password-reset endpoints. `make-offer`,
`accept-offer`, and `convert-to-enrollment` are staff-only RPC-style
actions, not an overloaded `PATCH`, per §1.
"""

from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from api.viewsets import TenantScopedModelViewSet
from apps.admissions import services
from apps.admissions.filters import ApplicationFilterSet
from apps.admissions.models import Application
from apps.admissions.serializers import (
    ApplicationSerializer,
    ConvertToEnrollmentSerializer,
    OfferSerializer,
)
from apps.permissions.permissions import HasPermission, IsInstitutionMember

_STAFF_ACTIONS = ("make_offer", "accept_offer", "convert_to_enrollment")


class ApplicationViewSet(TenantScopedModelViewSet):
    queryset_model = Application
    serializer_class = ApplicationSerializer
    filterset_class = ApplicationFilterSet

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        if self.action in _STAFF_ACTIONS:
            return [IsInstitutionMember(), HasPermission("admissions.application.manage")()]
        return [IsInstitutionMember()]

    def perform_create(self, serializer):
        serializer.instance = services.submit_application(
            institution=self.request.institution, **serializer.validated_data
        )

    @action(detail=True, methods=["post"], url_path="make-offer")
    def make_offer(self, request, pk=None):
        application = self.get_object()
        offer = services.make_offer(institution=request.institution, application=application)
        return Response(OfferSerializer(offer).data, status=201)

    @action(detail=True, methods=["post"], url_path="accept-offer")
    def accept_offer(self, request, pk=None):
        application = self.get_object()
        offer = application.offers.order_by("-offered_at").first()
        if offer is None:
            raise ValidationError({"detail": ["No offer exists for this application."]})
        offer = services.accept_offer(institution=request.institution, offer=offer)
        return Response(OfferSerializer(offer).data)

    @action(detail=True, methods=["post"], url_path="convert-to-enrollment")
    def convert_to_enrollment(self, request, pk=None):
        application = self.get_object()
        serializer = ConvertToEnrollmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            enrollment = services.convert_to_enrollment(
                institution=request.institution,
                application=application,
                **serializer.validated_data,
            )
        except ValueError as exc:
            raise ValidationError({"detail": [str(exc)]}) from exc
        return Response({"enrollment_id": str(enrollment.id)}, status=201)

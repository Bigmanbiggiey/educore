"""API views for `institutions` — docs/permissions.md §7. Every view here
is gated `IsPlatformStaff`, never `IsInstitutionMember`/`HasPermission`
(`Institution` itself has no tenant to scope against — it IS the tenancy
root). Deliberately no `destroy` action anywhere: `Institution`/`Domain`
have no safe delete path (a huge amount of tenant data references
`institution_id` as a plain cross-app UUID, not a real FK, so nothing
would cascade-clean it up) — not built until a real offboarding flow
exists, not an oversight.
"""

from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.core.permissions import IsPlatformStaff
from apps.institutions import services
from apps.institutions.models import Domain, Institution
from apps.institutions.serializers import (
    AddCustomDomainSerializer,
    DomainSerializer,
    InstitutionSerializer,
    ProvisionInstitutionSerializer,
    SetIsolationTierSerializer,
    VerifyDomainSerializer,
)


class InstitutionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsPlatformStaff]
    serializer_class = InstitutionSerializer
    queryset = Institution.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = ProvisionInstitutionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            institution = services.provision_institution(
                actor=request.user, **serializer.validated_data
            )
        except ValueError as exc:
            raise ValidationError({"detail": [str(exc)]}) from exc
        return Response(InstitutionSerializer(institution).data, status=201)

    @action(detail=True, methods=["post"], url_path="set-isolation-tier")
    def set_isolation_tier(self, request, pk=None):
        institution = self.get_object()
        serializer = SetIsolationTierSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            institution = services.set_isolation_tier(institution, **serializer.validated_data)
        except ValueError as exc:
            raise ValidationError({"detail": [str(exc)]}) from exc
        return Response(InstitutionSerializer(institution).data)

    @action(detail=True, methods=["post"])
    def domains(self, request, pk=None):
        institution = self.get_object()
        serializer = AddCustomDomainSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        domain = services.add_custom_domain(institution, **serializer.validated_data)
        return Response(DomainSerializer(domain).data, status=201)


class DomainViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsPlatformStaff]
    serializer_class = DomainSerializer
    queryset = Domain.objects.all()

    @action(detail=True, methods=["post"])
    def verify(self, request, pk=None):
        domain = self.get_object()
        serializer = VerifyDomainSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            domain = services.verify_domain(domain, **serializer.validated_data)
        except ValueError as exc:
            raise ValidationError({"detail": [str(exc)]}) from exc
        return Response(DomainSerializer(domain).data)

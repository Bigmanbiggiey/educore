"""API views for `transport` — docs/api-design.md. `TransportAssignment`
creation/update routes through `services.assign_transport` (it's
`update_or_create`-keyed on `student_id`, so "create" and "update" are the
same write here, same reasoning as `attendance.AttendanceRecordViewSet`).
`RouteViewSet.manifest` is an RPC-style read action surfacing
`selectors.get_route_manifest` over HTTP — the driver's pickup list is a
read-side aggregation, not something a plain list endpoint's shape can
represent.
"""

from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from api.viewsets import TenantScopedModelViewSet
from apps.permissions.permissions import HasPermission, IsInstitutionMember
from apps.transport import selectors, services
from apps.transport.filters import TransportAssignmentFilterSet
from apps.transport.models import Route, Stop, TransportAssignment, Vehicle
from apps.transport.serializers import (
    RouteManifestEntrySerializer,
    RouteSerializer,
    StopSerializer,
    TransportAssignmentSerializer,
    VehicleSerializer,
)

_WRITE_ACTIONS = ("create", "update", "partial_update", "destroy")


def _write_gated_by(permission_code):
    def get_permissions(self):
        if self.action in _WRITE_ACTIONS:
            return [IsInstitutionMember(), HasPermission(permission_code)()]
        return [IsInstitutionMember()]

    return get_permissions


class VehicleViewSet(TenantScopedModelViewSet):
    queryset_model = Vehicle
    serializer_class = VehicleSerializer
    get_permissions = _write_gated_by("transport.vehicle.manage")


class RouteViewSet(TenantScopedModelViewSet):
    queryset_model = Route
    serializer_class = RouteSerializer
    get_permissions = _write_gated_by("transport.route.manage")
    # `vehicle` is a real intra-app FK (see models.py's module docstring),
    # so this traverses cleanly.
    search_fields = ["name", "vehicle__registration_number"]

    @action(detail=True, methods=["get"])
    def manifest(self, request, pk=None):
        route = self.get_object()
        manifest = selectors.get_route_manifest(request.institution, route.id)
        return Response(RouteManifestEntrySerializer(manifest, many=True).data)


class StopViewSet(TenantScopedModelViewSet):
    queryset_model = Stop
    serializer_class = StopSerializer
    get_permissions = _write_gated_by("transport.stop.manage")


class TransportAssignmentViewSet(TenantScopedModelViewSet):
    queryset_model = TransportAssignment
    serializer_class = TransportAssignmentSerializer
    filterset_class = TransportAssignmentFilterSet
    get_permissions = _write_gated_by("transport.transport_assignment.manage")

    def create(self, request, *args, **kwargs):
        return self._assign(request)

    def update(self, request, *args, **kwargs):
        return self._assign(request)

    def _assign(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            assignment = services.assign_transport(
                institution=request.institution, **serializer.validated_data
            )
        except ValueError as exc:
            raise ValidationError({"detail": [str(exc)]}) from exc
        return Response(self.get_serializer(assignment).data, status=201)

"""API views for `hostel` — docs/api-design.md. `BedAllocation` creation
routes through `services.allocate_bed` (has to check the room's capacity
for the term before writing — the generic create path can't do that, same
reasoning as `library.LoanViewSet`). `RoomViewSet.occupancy` is an
RPC-style read action surfacing `selectors.get_occupancy` over HTTP, same
shape as `transport.RouteViewSet.manifest` — occupancy is a per-term
aggregate, not something a plain retrieve can represent, so it takes
`?term_id=` as a query parameter.
"""

import uuid

from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from api.viewsets import TenantScopedModelViewSet
from apps.hostel import selectors, services
from apps.hostel.filters import BedAllocationFilterSet
from apps.hostel.models import BedAllocation, Hostel, Room
from apps.hostel.serializers import (
    BedAllocationSerializer,
    HostelSerializer,
    RoomOccupancySerializer,
    RoomSerializer,
)
from apps.permissions.permissions import HasPermission, IsInstitutionMember

_WRITE_ACTIONS = ("create", "update", "partial_update", "destroy")


def _write_gated_by(permission_code):
    def get_permissions(self):
        if self.action in _WRITE_ACTIONS:
            return [IsInstitutionMember(), HasPermission(permission_code)()]
        return [IsInstitutionMember()]

    return get_permissions


class HostelViewSet(TenantScopedModelViewSet):
    queryset_model = Hostel
    serializer_class = HostelSerializer
    get_permissions = _write_gated_by("hostel.hostel.manage")


class RoomViewSet(TenantScopedModelViewSet):
    queryset_model = Room
    serializer_class = RoomSerializer
    get_permissions = _write_gated_by("hostel.room.manage")
    # `hostel` is a real intra-app FK (see models.py's module docstring),
    # so this traverses cleanly.
    search_fields = ["room_number", "hostel__name"]

    @action(detail=True, methods=["get"])
    def occupancy(self, request, pk=None):
        room = self.get_object()
        term_id = request.query_params.get("term_id")
        try:
            term_id = uuid.UUID(term_id) if term_id else None
        except ValueError as exc:
            raise ValidationError({"term_id": ["Must be a valid UUID."]}) from exc
        if term_id is None:
            raise ValidationError({"term_id": ["This query parameter is required."]})
        occupancy = selectors.get_occupancy(request.institution, room.id, term_id)
        return Response(RoomOccupancySerializer(occupancy).data)


class BedAllocationViewSet(TenantScopedModelViewSet):
    queryset_model = BedAllocation
    serializer_class = BedAllocationSerializer
    filterset_class = BedAllocationFilterSet
    get_permissions = _write_gated_by("hostel.bed_allocation.manage")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            allocation = services.allocate_bed(
                institution=request.institution, **serializer.validated_data
            )
        except ValueError as exc:
            raise ValidationError({"detail": [str(exc)]}) from exc
        return Response(self.get_serializer(allocation).data, status=201)

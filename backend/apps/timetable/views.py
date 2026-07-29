"""API views for `timetable` — docs/api-design.md. `Period` is nested under
its `Timetable` (`/api/v1/timetables/<id>/periods/`) since it has no
independent identity outside its parent — the one case §1 says nesting is
appropriate. `SubjectSlotAssignment` writes go through `services.assign_slot`
rather than the generic create path, since clash-detection has to run
first and `update_or_create` keyed on `period` means "create" and "update"
are the same operation here.
"""

from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from api.viewsets import TenantScopedModelViewSet
from apps.permissions.permissions import HasPermission, IsInstitutionMember
from apps.timetable.models import Period, SubjectSlotAssignment, Timetable
from apps.timetable.serializers import (
    PeriodSerializer,
    SubjectSlotAssignmentSerializer,
    TimetableSerializer,
)
from apps.timetable.services import assign_slot

_WRITE_ACTIONS = ("create", "update", "partial_update", "destroy")


def _write_gated_by(permission_code):
    def get_permissions(self):
        if self.action in _WRITE_ACTIONS:
            return [IsInstitutionMember(), HasPermission(permission_code)()]
        return [IsInstitutionMember()]

    return get_permissions


class TimetableViewSet(TenantScopedModelViewSet):
    queryset_model = Timetable
    serializer_class = TimetableSerializer
    get_permissions = _write_gated_by("timetable.timetable.manage")


class PeriodViewSet(TenantScopedModelViewSet):
    queryset_model = Period
    serializer_class = PeriodSerializer
    get_permissions = _write_gated_by("timetable.period.manage")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.get_base_queryset()
        return self.get_base_queryset().filter(timetable_id=self.kwargs["timetable_pk"])

    def perform_create(self, serializer):
        serializer.save(
            institution_id=self.request.institution.id, timetable_id=self.kwargs["timetable_pk"]
        )


class SubjectSlotAssignmentViewSet(TenantScopedModelViewSet):
    queryset_model = SubjectSlotAssignment
    serializer_class = SubjectSlotAssignmentSerializer
    get_permissions = _write_gated_by("timetable.subject_slot_assignment.manage")

    def create(self, request, *args, **kwargs):
        return self._assign(request)

    def update(self, request, *args, **kwargs):
        # `assign_slot` is `update_or_create`-keyed on `period`, so "create"
        # and "update" are the same write here — both must re-run
        # clash-detection, so neither goes through the generic save path.
        return self._assign(request)

    def _assign(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            assignment = assign_slot(institution=request.institution, **serializer.validated_data)
        except ValueError as exc:
            raise ValidationError({"staff_id": [str(exc)]}) from exc
        return Response(self.get_serializer(assignment).data, status=201)

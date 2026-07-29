"""API views for `attendance` — docs/api-design.md. Writes route through
`services.mark_attendance` rather than the generic save path — it's
`update_or_create`-keyed on (term, date, subject_type, target_id), so
"create" and "update" are the same operation, same pattern as
`timetable.SubjectSlotAssignmentViewSet`.
"""

from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from api.viewsets import TenantScopedModelViewSet
from apps.attendance.filters import AttendanceRecordFilterSet
from apps.attendance.models import AttendanceRecord
from apps.attendance.serializers import AttendanceRecordSerializer
from apps.attendance.services import mark_attendance
from apps.permissions.permissions import HasPermission, IsInstitutionMember

_WRITE_ACTIONS = ("create", "update", "partial_update", "destroy")


class AttendanceRecordViewSet(TenantScopedModelViewSet):
    queryset_model = AttendanceRecord
    serializer_class = AttendanceRecordSerializer
    filterset_class = AttendanceRecordFilterSet

    def get_permissions(self):
        if self.action in _WRITE_ACTIONS:
            return [IsInstitutionMember(), HasPermission("attendance.attendance_record.manage")()]
        return [IsInstitutionMember()]

    def create(self, request, *args, **kwargs):
        return self._mark(request)

    def update(self, request, *args, **kwargs):
        return self._mark(request)

    def _mark(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            record = mark_attendance(institution=request.institution, **serializer.validated_data)
        except ValueError as exc:
            raise ValidationError({"subject_type": [str(exc)]}) from exc
        return Response(self.get_serializer(record).data, status=201)

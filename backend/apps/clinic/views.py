"""API views for `clinic` — docs/api-design.md. Unlike every other Layer 1
app, reads here are *not* open to any active institution member — medical
data is sensitive enough that docs/modules.md calls out this app's
selectors as "access-restricted (nurse role only — enforced via
permissions)", so both reads and writes require an explicit permission
code (`clinic.{resource}.view` / `.manage`), typically granted only to the
seeded Nurse role — not the "any member reads, permission-holder writes"
default every other app in this codebase uses.

`HealthRecord` creation/update routes through `services.set_health_record`
(it's `update_or_create`-keyed on `student_id`, so "create" and "update"
are the same write here, same reasoning as
`attendance.AttendanceRecordViewSet`).
"""

from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from api.viewsets import TenantScopedModelViewSet
from apps.clinic import services
from apps.clinic.filters import ClinicVisitFilterSet, HealthRecordFilterSet, MedicationFilterSet
from apps.clinic.models import ClinicVisit, HealthRecord, Medication
from apps.clinic.serializers import (
    ClinicVisitSerializer,
    HealthRecordSerializer,
    MedicationSerializer,
)
from apps.permissions.permissions import HasPermission, IsInstitutionMember

_WRITE_ACTIONS = ("create", "update", "partial_update", "destroy")


def _restricted_to(resource: str):
    """Both reads and writes require a permission for this resource —
    `view` for reads, `manage` for writes — never the "any active member
    reads" default the rest of this codebase uses."""

    def get_permissions(self):
        if self.action in _WRITE_ACTIONS:
            return [IsInstitutionMember(), HasPermission(f"clinic.{resource}.manage")()]
        return [IsInstitutionMember(), HasPermission(f"clinic.{resource}.view")()]

    return get_permissions


class HealthRecordViewSet(TenantScopedModelViewSet):
    queryset_model = HealthRecord
    serializer_class = HealthRecordSerializer
    filterset_class = HealthRecordFilterSet
    get_permissions = _restricted_to("health_record")

    def create(self, request, *args, **kwargs):
        return self._set(request)

    def update(self, request, *args, **kwargs):
        return self._set(request)

    def _set(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            record = services.set_health_record(
                institution=request.institution, **serializer.validated_data
            )
        except ValueError as exc:
            raise ValidationError({"detail": [str(exc)]}) from exc
        return Response(self.get_serializer(record).data, status=201)


class ClinicVisitViewSet(TenantScopedModelViewSet):
    queryset_model = ClinicVisit
    serializer_class = ClinicVisitSerializer
    filterset_class = ClinicVisitFilterSet
    get_permissions = _restricted_to("clinic_visit")


class MedicationViewSet(TenantScopedModelViewSet):
    queryset_model = Medication
    serializer_class = MedicationSerializer
    filterset_class = MedicationFilterSet
    get_permissions = _restricted_to("medication")

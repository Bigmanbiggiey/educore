"""API views for `curriculum_tvet` — docs/api-design.md §8. `TVETDepartment`,
`Course`, `CompetencyUnit`, `IndustrialAttachment`, and `Certificate` all
get ordinary CRUD (the last two have no cross-curriculum equivalent, same
non-object-scoped precedent as `curriculum_cbc.Project`). Practical
assessment recording does NOT get its own endpoint here — that's
`academics.views.AssessmentRecordView`.
"""

from api.viewsets import TenantScopedModelViewSet
from apps.curriculum_tvet.models import (
    Certificate,
    CompetencyUnit,
    Course,
    IndustrialAttachment,
    TVETDepartment,
)
from apps.curriculum_tvet.serializers import (
    CertificateSerializer,
    CompetencyUnitSerializer,
    CourseSerializer,
    IndustrialAttachmentSerializer,
    TVETDepartmentSerializer,
)
from apps.permissions.permissions import HasPermission, IsInstitutionMember

_WRITE_ACTIONS = ("create", "update", "partial_update", "destroy")


def _write_gated_by(permission_code):
    def get_permissions(self):
        if self.action in _WRITE_ACTIONS:
            return [IsInstitutionMember(), HasPermission(permission_code)()]
        return [IsInstitutionMember()]

    return get_permissions


class TVETDepartmentViewSet(TenantScopedModelViewSet):
    queryset_model = TVETDepartment
    serializer_class = TVETDepartmentSerializer
    get_permissions = _write_gated_by("curriculum_tvet.department.manage")


class CourseViewSet(TenantScopedModelViewSet):
    queryset_model = Course
    serializer_class = CourseSerializer
    get_permissions = _write_gated_by("curriculum_tvet.course.manage")


class CompetencyUnitViewSet(TenantScopedModelViewSet):
    queryset_model = CompetencyUnit
    serializer_class = CompetencyUnitSerializer
    get_permissions = _write_gated_by("curriculum_tvet.competency_unit.manage")


class IndustrialAttachmentViewSet(TenantScopedModelViewSet):
    queryset_model = IndustrialAttachment
    serializer_class = IndustrialAttachmentSerializer
    get_permissions = _write_gated_by("curriculum_tvet.industrial_attachment.manage")


class CertificateViewSet(TenantScopedModelViewSet):
    queryset_model = Certificate
    serializer_class = CertificateSerializer
    get_permissions = _write_gated_by("curriculum_tvet.certificate.manage")

"""API views for `academics` — docs/api-design.md. Only `GradingScale` and
`SubjectCatalog` get CRUD endpoints — the `AssessmentEngine`/`ReportEngine`
contracts have no models and nothing to expose until Phase 3's curriculum
plugins implement them. Reads open to any active member (same as
`classes_streams`' reference data), writes gated by permission.
"""

from api.viewsets import TenantScopedModelViewSet
from apps.academics.models import GradingScale, SubjectCatalog
from apps.academics.serializers import GradingScaleSerializer, SubjectCatalogSerializer
from apps.permissions.permissions import HasPermission, IsInstitutionMember

_WRITE_ACTIONS = ("create", "update", "partial_update", "destroy")


def _write_gated_by(permission_code):
    def get_permissions(self):
        if self.action in _WRITE_ACTIONS:
            return [IsInstitutionMember(), HasPermission(permission_code)()]
        return [IsInstitutionMember()]

    return get_permissions


class GradingScaleViewSet(TenantScopedModelViewSet):
    queryset_model = GradingScale
    serializer_class = GradingScaleSerializer
    get_permissions = _write_gated_by("academics.grading_scale.manage")


class SubjectCatalogViewSet(TenantScopedModelViewSet):
    queryset_model = SubjectCatalog
    serializer_class = SubjectCatalogSerializer
    get_permissions = _write_gated_by("academics.subject_catalog.manage")

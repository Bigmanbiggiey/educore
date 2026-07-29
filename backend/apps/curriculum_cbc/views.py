"""API views for `curriculum_cbc` — docs/api-design.md §8: operations with
no cross-curriculum equivalent (CBC PCI/core-value management, learning
areas, competencies, projects) get their own dedicated endpoints here.
Assessment recording does NOT — that's the curriculum-agnostic
`/api/v1/assessments/` endpoint (`academics.views.AssessmentRecordView`).
"""

from api.viewsets import TenantScopedModelViewSet
from apps.curriculum_cbc.models import PCI, Competency, CoreValue, LearningArea, Project
from apps.curriculum_cbc.serializers import (
    CompetencySerializer,
    CoreValueSerializer,
    LearningAreaSerializer,
    PCISerializer,
    ProjectSerializer,
)
from apps.permissions.permissions import HasPermission, IsInstitutionMember

_WRITE_ACTIONS = ("create", "update", "partial_update", "destroy")


def _write_gated_by(permission_code):
    def get_permissions(self):
        if self.action in _WRITE_ACTIONS:
            return [IsInstitutionMember(), HasPermission(permission_code)()]
        return [IsInstitutionMember()]

    return get_permissions


class LearningAreaViewSet(TenantScopedModelViewSet):
    queryset_model = LearningArea
    serializer_class = LearningAreaSerializer
    get_permissions = _write_gated_by("curriculum_cbc.learning_area.manage")


class CompetencyViewSet(TenantScopedModelViewSet):
    queryset_model = Competency
    serializer_class = CompetencySerializer
    get_permissions = _write_gated_by("curriculum_cbc.competency.manage")


class CoreValueViewSet(TenantScopedModelViewSet):
    queryset_model = CoreValue
    serializer_class = CoreValueSerializer
    get_permissions = _write_gated_by("curriculum_cbc.core_value.manage")


class PCIViewSet(TenantScopedModelViewSet):
    queryset_model = PCI
    serializer_class = PCISerializer
    get_permissions = _write_gated_by("curriculum_cbc.pci.manage")


class ProjectViewSet(TenantScopedModelViewSet):
    queryset_model = Project
    serializer_class = ProjectSerializer
    get_permissions = _write_gated_by("curriculum_cbc.project.manage")

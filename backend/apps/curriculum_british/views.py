"""API views for `curriculum_british` — docs/api-design.md §8. `YearGroup`
and `Subject` get ordinary CRUD. `PredictedGrade` also gets a dedicated
endpoint (no cross-curriculum equivalent) but writes route through
`services.set_predicted_grade`, since setting the same subject+academic_year
twice updates in place rather than duplicating. `Coursework` recording does
NOT get its own endpoint here — that's `academics.views.AssessmentRecordView`.
"""

from rest_framework.response import Response

from api.viewsets import TenantScopedModelViewSet
from apps.curriculum_british import services
from apps.curriculum_british.models import PredictedGrade, Subject, YearGroup
from apps.curriculum_british.serializers import (
    BritishSubjectSerializer,
    PredictedGradeSerializer,
    YearGroupSerializer,
)
from apps.permissions.permissions import HasPermission, IsInstitutionMember

_WRITE_ACTIONS = ("create", "update", "partial_update", "destroy")


def _write_gated_by(permission_code):
    def get_permissions(self):
        if self.action in _WRITE_ACTIONS:
            return [IsInstitutionMember(), HasPermission(permission_code)()]
        return [IsInstitutionMember()]

    return get_permissions


class YearGroupViewSet(TenantScopedModelViewSet):
    queryset_model = YearGroup
    serializer_class = YearGroupSerializer
    get_permissions = _write_gated_by("curriculum_british.year_group.manage")


class SubjectViewSet(TenantScopedModelViewSet):
    queryset_model = Subject
    serializer_class = BritishSubjectSerializer
    get_permissions = _write_gated_by("curriculum_british.subject.manage")


class PredictedGradeViewSet(TenantScopedModelViewSet):
    queryset_model = PredictedGrade
    serializer_class = PredictedGradeSerializer
    get_permissions = _write_gated_by("curriculum_british.predicted_grade.manage")

    def create(self, request, *args, **kwargs):
        return self._set(request)

    def update(self, request, *args, **kwargs):
        return self._set(request)

    def _set(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        grade = services.set_predicted_grade(
            institution=request.institution,
            student_id=data["student_id"],
            subject=data["subject"],
            academic_year_id=data["academic_year_id"],
            predicted_grade=data["predicted_grade"],
            set_by=request.user.id,
        )
        return Response(self.get_serializer(grade).data, status=201)

"""API views for `curriculum_844` — docs/api-design.md §8. `Subject` gets
ordinary CRUD. `recompute-mean-grades` and `kcpe-kcse-results/import` have
no cross-curriculum equivalent, so they get dedicated endpoints here rather
than living on the generic `academics` endpoint set. Assessment recording
does NOT get its own endpoint here — that's
`academics.views.AssessmentRecordView`.
"""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from api.viewsets import TenantScopedModelViewSet
from apps.curriculum_844 import services
from apps.curriculum_844.models import Subject
from apps.curriculum_844.serializers import (
    KcpeKcseImportRequestSerializer,
    RecomputeMeanGradesRequestSerializer,
    SubjectSerializer,
)
from apps.curriculum_844.tasks import recompute_mean_grades_task
from apps.permissions.permissions import HasPermission, IsInstitutionMember

_WRITE_ACTIONS = ("create", "update", "partial_update", "destroy")


def _write_gated_by(permission_code):
    def get_permissions(self):
        if self.action in _WRITE_ACTIONS:
            return [IsInstitutionMember(), HasPermission(permission_code)()]
        return [IsInstitutionMember()]

    return get_permissions


class SubjectViewSet(TenantScopedModelViewSet):
    queryset_model = Subject
    serializer_class = SubjectSerializer
    get_permissions = _write_gated_by("curriculum_844.subject.manage")


class RecomputeMeanGradesView(APIView):
    """Enqueues the Celery task that recomputes `MeanGradeSnapshot` for
    every actively-enrolled student in a class — ranking needs everyone
    recomputed together, so this is an explicit administrative action, not
    something that happens automatically on every `ExamResult` write."""

    permission_classes = [
        IsInstitutionMember,
        HasPermission("curriculum_844.mean_grade.recompute"),
    ]

    @extend_schema(
        request=RecomputeMeanGradesRequestSerializer, responses={202: OpenApiTypes.OBJECT}
    )
    def post(self, request):
        serializer = RecomputeMeanGradesRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        recompute_mean_grades_task.delay(
            str(request.institution.id), str(data["term_id"]), str(data["class_grade_id"])
        )
        return Response({"detail": "Recompute enqueued."}, status=202)


class KcpeKcseResultImportView(APIView):
    permission_classes = [
        IsInstitutionMember,
        HasPermission("curriculum_844.kcpe_kcse_result.import"),
    ]

    @extend_schema(request=KcpeKcseImportRequestSerializer, responses={201: OpenApiTypes.OBJECT})
    def post(self, request):
        serializer = KcpeKcseImportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            results = services.import_kcpe_kcse_results(
                institution=request.institution, term_id=data["term_id"], rows=data["rows"]
            )
        except ValueError as exc:
            raise ValidationError({"rows": [str(exc)]}) from exc
        return Response({"created": len(results)}, status=201)

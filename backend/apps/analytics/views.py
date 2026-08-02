"""API views for `analytics` — docs/api-design.md. The three rollup
ViewSets are read-only (`api.viewsets.TenantScopedReadOnlyModelViewSet`) —
these rows are Celery-computed, never client-written. `RecomputeRollupsView`
enqueues the Celery task that (re)computes one class's rollups, mirroring
`curriculum_844.views.RecomputeMeanGradesView`'s "explicit administrative
action" shape exactly — ranking-adjacent aggregates need everyone in the
class recomputed together, not per-write.

Each rollup ViewSet also accepts `?format=csv`/`?format=xlsx`
(docs/roadmap.md Phase 8's "Exports: PDF, Excel, CSV" — PDF is `reports`'s
job) via `api.renderers`, DRF's standard content-negotiation mechanism
rather than a bespoke export endpoint.
"""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from api.renderers import CSVRenderer, XLSXRenderer
from api.viewsets import TenantScopedReadOnlyModelViewSet
from apps.analytics.filters import (
    AttendanceRateSnapshotFilterSet,
    FeeCollectionSnapshotFilterSet,
    MeanGradeRollupFilterSet,
)
from apps.analytics.models import AttendanceRateSnapshot, FeeCollectionSnapshot, MeanGradeRollup
from apps.analytics.serializers import (
    AttendanceRateSnapshotSerializer,
    FeeCollectionSnapshotSerializer,
    MeanGradeRollupSerializer,
    RecomputeRollupsRequestSerializer,
)
from apps.analytics.tasks import recompute_class_rollups_task
from apps.permissions.permissions import HasPermission, IsInstitutionMember

_EXPORTABLE_RENDERER_CLASSES = [JSONRenderer, BrowsableAPIRenderer, CSVRenderer, XLSXRenderer]


class AttendanceRateSnapshotViewSet(TenantScopedReadOnlyModelViewSet):
    queryset_model = AttendanceRateSnapshot
    serializer_class = AttendanceRateSnapshotSerializer
    filterset_class = AttendanceRateSnapshotFilterSet
    permission_classes = [IsInstitutionMember]
    renderer_classes = _EXPORTABLE_RENDERER_CLASSES


class FeeCollectionSnapshotViewSet(TenantScopedReadOnlyModelViewSet):
    queryset_model = FeeCollectionSnapshot
    serializer_class = FeeCollectionSnapshotSerializer
    filterset_class = FeeCollectionSnapshotFilterSet
    permission_classes = [IsInstitutionMember]
    renderer_classes = _EXPORTABLE_RENDERER_CLASSES


class MeanGradeRollupViewSet(TenantScopedReadOnlyModelViewSet):
    queryset_model = MeanGradeRollup
    serializer_class = MeanGradeRollupSerializer
    filterset_class = MeanGradeRollupFilterSet
    permission_classes = [IsInstitutionMember]
    renderer_classes = _EXPORTABLE_RENDERER_CLASSES


class RecomputeRollupsView(APIView):
    permission_classes = [IsInstitutionMember, HasPermission("analytics.rollup.recompute")]

    @extend_schema(request=RecomputeRollupsRequestSerializer, responses={202: OpenApiTypes.OBJECT})
    def post(self, request):
        serializer = RecomputeRollupsRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        recompute_class_rollups_task.delay(
            str(request.institution.id), str(data["class_grade_id"]), str(data["term_id"])
        )
        return Response({"detail": "Recompute enqueued."}, status=202)

"""Request/response shapes for `analytics`'s API surface — docs/api-design.md.
All three rollup serializers are read-only end to end — these rows are
machine-written by `services.compute_rollups`, never client-submitted, same
"no writable fields on a derived record" shape `admissions.Application.stage`
established for a narrower case.
"""

from rest_framework import serializers

from api.serializers import TenantScopedModelSerializer
from apps.analytics.models import AttendanceRateSnapshot, FeeCollectionSnapshot, MeanGradeRollup


class AttendanceRateSnapshotSerializer(TenantScopedModelSerializer):
    class Meta:
        model = AttendanceRateSnapshot
        fields = ["id", "class_grade_id", "term_id", "rate", "created_at", "updated_at"]
        read_only_fields = fields


class FeeCollectionSnapshotSerializer(TenantScopedModelSerializer):
    class Meta:
        model = FeeCollectionSnapshot
        fields = [
            "id",
            "class_grade_id",
            "term_id",
            "total_due",
            "total_collected",
            "collection_rate",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class MeanGradeRollupSerializer(TenantScopedModelSerializer):
    class Meta:
        model = MeanGradeRollup
        fields = [
            "id",
            "class_grade_id",
            "term_id",
            "mean_score",
            "mean_grade",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class RecomputeRollupsRequestSerializer(serializers.Serializer):
    class_grade_id = serializers.UUIDField()
    term_id = serializers.UUIDField()

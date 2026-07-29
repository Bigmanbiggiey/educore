"""Request/response shapes for `curriculum_844`'s API surface —
docs/api-design.md. No `ExamResult` serializer here — recording goes
through the curriculum-agnostic `academics.AssessmentRecordView`
(docs/api-design.md §8), not a curriculum-specific endpoint.
"""

from rest_framework import serializers

from api.serializers import TenantScopedModelSerializer
from apps.curriculum_844.models import Subject


class SubjectSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "subject_catalog_id", "name", "code", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "subject_catalog_id": {
                "help_text": "The generic subject this specializes (academics.SubjectCatalog)."
            },
            "name": {"help_text": "e.g. 'Mathematics'."},
            "code": {"help_text": "Short unique code, e.g. 'MATH'."},
        }


class RecomputeMeanGradesRequestSerializer(serializers.Serializer):
    term_id = serializers.UUIDField()
    class_grade_id = serializers.UUIDField()


class KcpeKcseResultRowSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    subject_id = serializers.UUIDField()
    score = serializers.DecimalField(max_digits=5, decimal_places=2)
    max_score = serializers.DecimalField(max_digits=5, decimal_places=2)


class KcpeKcseImportRequestSerializer(serializers.Serializer):
    term_id = serializers.UUIDField()
    rows = KcpeKcseResultRowSerializer(many=True)

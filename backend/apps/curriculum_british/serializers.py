"""Request/response shapes for `curriculum_british`'s API surface —
docs/api-design.md. No `Coursework` serializer here — recording goes
through the curriculum-agnostic `academics.AssessmentRecordView`
(docs/api-design.md §8), not a curriculum-specific endpoint.
"""

from api.serializers import TenantScopedModelSerializer
from apps.curriculum_british.models import PredictedGrade, Subject, YearGroup


class YearGroupSerializer(TenantScopedModelSerializer):
    class Meta:
        model = YearGroup
        fields = ["id", "class_grade_id", "key_stage", "name", "order", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "class_grade_id": {
                "help_text": "The class grade this specializes (classes_streams.ClassGrade)."
            },
            "name": {"help_text": "e.g. 'Year 7'."},
        }


class BritishSubjectSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Subject
        fields = [
            "id",
            "subject_catalog_id",
            "name",
            "code",
            "qualification_level",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PredictedGradeSerializer(TenantScopedModelSerializer):
    class Meta:
        model = PredictedGrade
        fields = [
            "id",
            "student_id",
            "subject",
            "academic_year_id",
            "predicted_grade",
            "set_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "set_by", "created_at", "updated_at"]

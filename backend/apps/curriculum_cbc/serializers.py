"""Request/response shapes for `curriculum_cbc`'s API surface —
docs/api-design.md. No `ContinuousAssessment` serializer here — assessment
recording goes through the curriculum-agnostic `academics.AssessmentRecordView`
(docs/api-design.md §8), not a CBC-specific endpoint.
"""

from api.serializers import TenantScopedModelSerializer
from apps.curriculum_cbc.models import PCI, Competency, CoreValue, LearningArea, Project


class LearningAreaSerializer(TenantScopedModelSerializer):
    class Meta:
        model = LearningArea
        fields = ["id", "subject_catalog_id", "name", "code", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "subject_catalog_id": {
                "help_text": "The generic subject this specializes (academics.SubjectCatalog)."
            },
            "name": {"help_text": "e.g. 'Environmental Activities'."},
            "code": {"help_text": "Short unique code, e.g. 'ENV'."},
        }


class CompetencySerializer(TenantScopedModelSerializer):
    class Meta:
        model = Competency
        fields = ["id", "learning_area", "strand", "sub_strand", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class CoreValueSerializer(TenantScopedModelSerializer):
    class Meta:
        model = CoreValue
        fields = ["id", "name", "description", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class PCISerializer(TenantScopedModelSerializer):
    class Meta:
        model = PCI
        fields = ["id", "name", "description", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProjectSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Project
        fields = [
            "id",
            "student_id",
            "competency",
            "term_id",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

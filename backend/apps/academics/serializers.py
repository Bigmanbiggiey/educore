from api.serializers import TenantScopedModelSerializer
from apps.academics.models import GradingScale, SubjectCatalog


class GradingScaleSerializer(TenantScopedModelSerializer):
    class Meta:
        model = GradingScale
        fields = ["id", "curriculum_type", "levels", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "curriculum_type": {"help_text": "Which curriculum this grading scale applies to."},
            "levels": {
                "help_text": "Ordered list of performance levels, e.g. [{'label', 'min', 'max'}].",
                "required": False,
            },
        }


class SubjectCatalogSerializer(TenantScopedModelSerializer):
    class Meta:
        model = SubjectCatalog
        fields = ["id", "curriculum_type", "name", "code", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "curriculum_type": {"help_text": "Which curriculum this subject belongs to."},
            "name": {"help_text": "e.g. 'Mathematics'."},
            "code": {"help_text": "Short unique code, e.g. 'MATH'."},
        }

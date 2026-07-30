"""Request/response shapes for `curriculum_tvet`'s API surface —
docs/api-design.md. No `PracticalAssessment` serializer here — recording
goes through the curriculum-agnostic `academics.AssessmentRecordView`
(docs/api-design.md §8), not a curriculum-specific endpoint.
"""

from api.serializers import TenantScopedModelSerializer
from apps.curriculum_tvet.models import (
    Certificate,
    CompetencyUnit,
    Course,
    IndustrialAttachment,
    TVETDepartment,
)


class TVETDepartmentSerializer(TenantScopedModelSerializer):
    class Meta:
        model = TVETDepartment
        fields = ["id", "name", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class CourseSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Course
        fields = ["id", "department", "course_code", "name", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class CompetencyUnitSerializer(TenantScopedModelSerializer):
    class Meta:
        model = CompetencyUnit
        fields = ["id", "course", "unit_code", "name", "credit_hours", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class IndustrialAttachmentSerializer(TenantScopedModelSerializer):
    class Meta:
        model = IndustrialAttachment
        fields = [
            "id",
            "student_id",
            "host_organization",
            "start_date",
            "end_date",
            "supervisor_report",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CertificateSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Certificate
        fields = [
            "id",
            "student_id",
            "course",
            "issued_at",
            "certificate_number",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {"issued_at": {"required": False}}

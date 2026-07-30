"""Request/response shapes for `curriculum_university`'s API surface —
docs/api-design.md. No `UnitAssessment` serializer here — recording goes
through the curriculum-agnostic `academics.AssessmentRecordView`
(docs/api-design.md §8), not a curriculum-specific endpoint.
"""

from rest_framework import serializers

from api.serializers import TenantScopedModelSerializer
from apps.curriculum_university.models import (
    CourseRegistration,
    Dissertation,
    Faculty,
    Graduation,
    Programme,
    School,
    Semester,
    Unit,
    UniversityDepartment,
)


class FacultySerializer(TenantScopedModelSerializer):
    class Meta:
        model = Faculty
        fields = ["id", "name", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class SchoolSerializer(TenantScopedModelSerializer):
    class Meta:
        model = School
        fields = ["id", "faculty", "name", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class UniversityDepartmentSerializer(TenantScopedModelSerializer):
    class Meta:
        model = UniversityDepartment
        fields = ["id", "school", "name", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProgrammeSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Programme
        fields = [
            "id",
            "department",
            "programme_code",
            "degree_level",
            "name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class UnitSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Unit
        fields = [
            "id",
            "programme",
            "unit_code",
            "name",
            "credit_hours",
            "semester_offered",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SemesterSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Semester
        fields = ["id", "term_id", "number", "name", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "term_id": {"help_text": "The term this semester specializes (classes_streams.Term)."},
        }


class CourseRegistrationSerializer(TenantScopedModelSerializer):
    class Meta:
        model = CourseRegistration
        fields = ["id", "student_id", "unit", "semester", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class DissertationSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Dissertation
        fields = [
            "id",
            "student_id",
            "supervisor_id",
            "title",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class GraduationSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Graduation
        fields = [
            "id",
            "student_id",
            "programme",
            "conferred_at",
            "classification",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RecomputeGpaRequestSerializer(serializers.Serializer):
    semester_id = serializers.UUIDField()

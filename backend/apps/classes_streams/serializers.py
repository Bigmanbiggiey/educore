"""Request/response shapes for `classes_streams`'s API surface —
docs/api-design.md. `institution` never appears as a field — it's resolved
server-side from the `Host` header (§7), never client-supplied. `is_current`
on `Term` is read-only here — it's only ever changed via the dedicated
`set-current` RPC action, not an overloaded `PATCH` (§1).
"""

from api.serializers import TenantScopedModelSerializer
from apps.classes_streams.models import (
    AcademicYear,
    ClassGrade,
    ClassTeacherAssignment,
    Stream,
    Term,
)


class AcademicYearSerializer(TenantScopedModelSerializer):
    class Meta:
        model = AcademicYear
        fields = ["id", "year_label", "start_date", "end_date", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "year_label": {"help_text": "Human-readable label, e.g. '2026'."},
            "start_date": {"help_text": "First day of the academic year."},
            "end_date": {"help_text": "Last day of the academic year."},
        }


class TermSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Term
        fields = [
            "id",
            "academic_year",
            "name",
            "start_date",
            "end_date",
            "is_current",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "is_current", "created_at", "updated_at"]
        extra_kwargs = {
            "academic_year": {"help_text": "The academic year this term belongs to."},
            "name": {"help_text": "e.g. 'Term 1'."},
            "start_date": {"help_text": "First day of the term."},
            "end_date": {"help_text": "Last day of the term."},
        }


class ClassGradeSerializer(TenantScopedModelSerializer):
    class Meta:
        model = ClassGrade
        fields = ["id", "term", "name", "curriculum_type", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "term": {"help_text": "The term this class grade is offered in."},
            "name": {"help_text": "e.g. 'Grade 4' or 'Form 2'."},
            "curriculum_type": {
                "help_text": "Which of the institution's curricula this belongs to."
            },
        }


class StreamSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Stream
        fields = ["id", "class_grade", "name", "capacity", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "class_grade": {"help_text": "The class grade this stream belongs to."},
            "name": {"help_text": "e.g. 'East' or 'Blue'."},
            "capacity": {
                "help_text": "Maximum number of students, if this stream is capped.",
                "required": False,
            },
        }


class ClassTeacherAssignmentSerializer(TenantScopedModelSerializer):
    class Meta:
        model = ClassTeacherAssignment
        fields = ["id", "class_grade", "stream", "term", "staff_id", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "class_grade": {"help_text": "The class grade being assigned a class teacher."},
            "stream": {
                "help_text": (
                    "The specific stream, if this assignment is per-stream rather than "
                    "per-class-grade."
                ),
                "required": False,
            },
            "term": {"help_text": "The term this assignment applies to."},
            "staff_id": {"help_text": "The assigned staff member's ID (staff.StaffProfile)."},
        }

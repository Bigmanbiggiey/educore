"""Request/response shapes for `attendance`'s API surface — docs/api-design.md."""

from api.serializers import TenantScopedModelSerializer
from apps.attendance.models import AttendanceRecord


class AttendanceRecordSerializer(TenantScopedModelSerializer):
    class Meta:
        model = AttendanceRecord
        fields = [
            "id",
            "term_id",
            "date",
            "subject_type",
            "target_id",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "term_id": {"help_text": "The term this record belongs to (classes_streams.Term)."},
            "date": {"help_text": "The date being marked."},
            "subject_type": {"help_text": "Whether target_id is a Student or a Staff member."},
            "target_id": {
                "help_text": "students.Student.id or staff.StaffProfile.id, per subject_type."
            },
            "status": {"help_text": "present, absent, late, or excused."},
        }

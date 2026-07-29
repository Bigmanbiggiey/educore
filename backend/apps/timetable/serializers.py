"""Request/response shapes for `timetable`'s API surface — docs/api-design.md.
`Period.timetable` is deliberately not a field here — it's resolved from
the nested URL (`/api/v1/timetables/<id>/periods/`), never client-supplied,
same reasoning docs/api-design.md §7 gives for `institution` never
appearing as a field.
"""

from api.serializers import TenantScopedModelSerializer
from apps.timetable.models import Period, SubjectSlotAssignment, Timetable


class TimetableSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Timetable
        fields = ["id", "term_id", "class_grade_id", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "term_id": {"help_text": "The term this timetable applies to (classes_streams.Term)."},
            "class_grade_id": {
                "help_text": "The class grade this belongs to (classes_streams.ClassGrade)."
            },
        }


class PeriodSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Period
        fields = ["id", "day_of_week", "start_time", "end_time", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "day_of_week": {"help_text": "0=Monday through 6=Sunday."},
            "start_time": {"help_text": "First minute of the period."},
            "end_time": {"help_text": "Last minute of the period."},
        }


class SubjectSlotAssignmentSerializer(TenantScopedModelSerializer):
    class Meta:
        model = SubjectSlotAssignment
        fields = ["id", "period", "subject_id", "staff_id", "room", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "period": {"help_text": "The period being assigned a subject/staff/room."},
            "subject_id": {"help_text": "The subject taught (academics.SubjectCatalog)."},
            "staff_id": {"help_text": "The teaching staff member (staff.StaffProfile)."},
            "room": {"help_text": "Room name/number, if tracked.", "required": False},
        }

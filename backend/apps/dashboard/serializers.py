"""Response shapes for `dashboard`'s API surface — docs/api-design.md.
`selectors.py` returns plain dicts (this app has no models), but the shape
of each dict is fixed and worth real serializers rather than
`OpenApiTypes.OBJECT` — an untyped placeholder generates an untyped
`{[key: string]: unknown}` on the frontend, defeating the whole point of
generating API types instead of hand-writing them. Same reasoning
`transport.RouteManifestEntrySerializer`/`hostel.RoomOccupancySerializer`
already established for a non-model dict response.
"""

from rest_framework import serializers


class PrincipalDashboardSerializer(serializers.Serializer):
    class_count = serializers.IntegerField()
    average_attendance_rate = serializers.DecimalField(
        max_digits=5, decimal_places=4, allow_null=True
    )
    average_collection_rate = serializers.DecimalField(
        max_digits=5, decimal_places=4, allow_null=True
    )


class _ScheduleEntrySerializer(serializers.Serializer):
    day_of_week = serializers.IntegerField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    subject_id = serializers.UUIDField()
    room = serializers.CharField()


class TeacherDashboardSerializer(serializers.Serializer):
    schedule = _ScheduleEntrySerializer(many=True)


class _ParentDashboardChildSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    admission_number = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    balance = serializers.DecimalField(max_digits=12, decimal_places=2)


class ParentDashboardSerializer(serializers.Serializer):
    children = _ParentDashboardChildSerializer(many=True)


class _StudentDashboardDocumentSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    minio_object_key = serializers.CharField()


class StudentDashboardSerializer(serializers.Serializer):
    attendance_rate = serializers.FloatField(allow_null=True)
    balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    documents = _StudentDashboardDocumentSerializer(many=True)

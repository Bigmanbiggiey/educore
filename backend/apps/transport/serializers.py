"""Request/response shapes for `transport`'s API surface — docs/api-design.md."""

from rest_framework import serializers

from api.serializers import TenantScopedModelSerializer
from apps.transport.models import Route, Stop, TransportAssignment, Vehicle


class VehicleSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Vehicle
        fields = [
            "id",
            "registration_number",
            "make_model",
            "capacity",
            "driver_name",
            "driver_phone",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RouteSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Route
        fields = ["id", "vehicle", "name", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class StopSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Stop
        fields = ["id", "route", "name", "sequence", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class TransportAssignmentSerializer(TenantScopedModelSerializer):
    class Meta:
        model = TransportAssignment
        fields = ["id", "student_id", "route", "stop", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "student_id": {"help_text": "students.Student.id."},
        }


class RouteManifestEntrySerializer(serializers.Serializer):
    stop_id = serializers.UUIDField()
    name = serializers.CharField()
    sequence = serializers.IntegerField()
    student_ids = serializers.ListField(child=serializers.UUIDField())

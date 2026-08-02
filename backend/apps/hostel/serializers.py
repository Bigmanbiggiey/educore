"""Request/response shapes for `hostel`'s API surface — docs/api-design.md."""

from rest_framework import serializers

from api.serializers import TenantScopedModelSerializer
from apps.hostel.models import BedAllocation, Hostel, Room


class HostelSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Hostel
        fields = ["id", "name", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class RoomSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Room
        fields = ["id", "hostel", "room_number", "capacity", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class BedAllocationSerializer(TenantScopedModelSerializer):
    class Meta:
        model = BedAllocation
        fields = ["id", "room", "student_id", "term_id", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "student_id": {"help_text": "students.Student.id."},
            "term_id": {"help_text": "classes_streams.Term.id."},
        }


class RoomOccupancySerializer(serializers.Serializer):
    capacity = serializers.IntegerField()
    occupied = serializers.IntegerField()
    available = serializers.IntegerField()

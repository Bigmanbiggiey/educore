"""Request/response shapes for `clinic`'s API surface — docs/api-design.md."""

from api.serializers import TenantScopedModelSerializer
from apps.clinic.models import ClinicVisit, HealthRecord, Medication


class HealthRecordSerializer(TenantScopedModelSerializer):
    class Meta:
        model = HealthRecord
        fields = [
            "id",
            "student_id",
            "allergies",
            "conditions",
            "blood_group",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "student_id": {"help_text": "students.Student.id."},
        }


class ClinicVisitSerializer(TenantScopedModelSerializer):
    class Meta:
        model = ClinicVisit
        fields = [
            "id",
            "student_id",
            "visit_date",
            "treated_by_id",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "student_id": {"help_text": "students.Student.id."},
            "treated_by_id": {"help_text": "staff.StaffProfile.id of the treating nurse."},
        }


class MedicationSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Medication
        fields = ["id", "visit", "name", "dosage", "notes", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

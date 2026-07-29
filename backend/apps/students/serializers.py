"""Request/response shapes for `students`'s API surface —
docs/api-design.md. `institution` never appears as a field — resolved
server-side from the `Host` header (§7).
"""

from api.serializers import TenantScopedModelSerializer
from apps.students.models import Enrollment, GuardianRelationship, Student


class StudentSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Student
        fields = [
            "id",
            "user_id",
            "admission_number",
            "first_name",
            "last_name",
            "date_of_birth",
            "gender",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "user_id": {
                "help_text": (
                    "The student's own login, if they have one — young students often don't."
                ),
                "required": False,
            },
            "admission_number": {"help_text": "Unique within the institution."},
            "first_name": {"help_text": "Student's first name."},
            "last_name": {"help_text": "Student's last name."},
            "date_of_birth": {"help_text": "Student's date of birth.", "required": False},
            "gender": {"help_text": "Student's gender, if recorded.", "required": False},
        }


class EnrollmentSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Enrollment
        fields = [
            "id",
            "student",
            "class_grade_id",
            "stream_id",
            "term_id",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "student": {"help_text": "The enrolled student."},
            "class_grade_id": {"help_text": "The class grade this enrollment is for."},
            "stream_id": {
                "help_text": "The specific stream, if stream allocation has happened yet.",
                "required": False,
            },
            "term_id": {"help_text": "The term this enrollment applies to."},
            "status": {"help_text": "Current enrollment status."},
        }


class GuardianRelationshipSerializer(TenantScopedModelSerializer):
    class Meta:
        model = GuardianRelationship
        fields = [
            "id",
            "student",
            "guardian_user_id",
            "relationship_type",
            "is_primary_contact",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "student": {"help_text": "The student this guardian is linked to."},
            "guardian_user_id": {"help_text": "The guardian's user ID (accounts.User)."},
            "relationship_type": {"help_text": "How this guardian relates to the student."},
            "is_primary_contact": {
                "help_text": "Whether this guardian is the primary contact for the student.",
                "required": False,
            },
        }

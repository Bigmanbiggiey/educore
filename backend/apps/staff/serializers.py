"""Request/response shapes for `staff`'s API surface — docs/api-design.md.
`institution` never appears as a field — resolved server-side from the
`Host` header (§7).
"""

from api.serializers import TenantScopedModelSerializer
from apps.staff.models import StaffProfile


class StaffProfileSerializer(TenantScopedModelSerializer):
    class Meta:
        model = StaffProfile
        fields = [
            "id",
            "user_id",
            "employee_number",
            "first_name",
            "last_name",
            "department",
            "employment_type",
            "hire_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "user_id": {"help_text": "This staff member's login (accounts.User)."},
            "employee_number": {"help_text": "Unique within the institution."},
            "first_name": {"help_text": "Staff member's first name."},
            "last_name": {"help_text": "Staff member's last name."},
            "department": {"help_text": "Department name, if assigned.", "required": False},
            "employment_type": {"help_text": "Full-time, part-time, or contract."},
            "hire_date": {"help_text": "Date this staff member was hired.", "required": False},
        }

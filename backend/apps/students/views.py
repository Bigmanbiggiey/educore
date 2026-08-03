"""API views for `students` — docs/api-design.md. Reads/writes require a
permission code specific to the resource (docs/permissions.md §1); `Student`
reads are additionally object-scoped for Parent/Student roles — two
independent layers, not folded into one check, per docs/permissions.md §3's
explicit defense-in-depth rationale: a bug in the permission check doesn't
automatically mean a bug in the queryset scope, and vice versa.
"""

from api.viewsets import TenantScopedModelViewSet
from apps.permissions.permissions import HasPermission, IsInstitutionMember
from apps.permissions.selectors import get_membership_access
from apps.students.models import Enrollment, GuardianRelationship, Student
from apps.students.selectors import get_guardian_children
from apps.students.serializers import (
    EnrollmentSerializer,
    GuardianRelationshipSerializer,
    StudentSerializer,
)

_WRITE_ACTIONS = ("create", "update", "partial_update", "destroy")


def _write_gated_by(permission_code):
    """Returns a `get_permissions` method: any active member holding
    `permission_code` may read; only that same permission gates writes too
    (unlike `classes_streams`, reads aren't open to every member here —
    student data is more sensitive than the academic calendar)."""

    def get_permissions(self):
        return [IsInstitutionMember(), HasPermission(permission_code)()]

    return get_permissions


class StudentViewSet(TenantScopedModelViewSet):
    queryset_model = Student
    serializer_class = StudentSerializer
    get_permissions = _write_gated_by("students.student.manage")
    search_fields = ["admission_number", "first_name", "last_name"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.get_base_queryset()

        access = get_membership_access(self.request.user, self.request.institution)
        # A Parent never sees the whole roster, even if some other grant
        # also gives them a broader view permission — fail closed
        # (docs/permissions.md §3: Parent is scoped to their own children,
        # full stop).
        if "Parent" in access.role_names:
            return get_guardian_children(self.request.user.id)
        if "Student" in access.role_names:
            return self.get_base_queryset().filter(user_id=self.request.user.id)
        return self.get_base_queryset()


class EnrollmentViewSet(TenantScopedModelViewSet):
    queryset_model = Enrollment
    serializer_class = EnrollmentSerializer
    get_permissions = _write_gated_by("students.enrollment.manage")


class GuardianRelationshipViewSet(TenantScopedModelViewSet):
    queryset_model = GuardianRelationship
    serializer_class = GuardianRelationshipSerializer
    get_permissions = _write_gated_by("students.guardian_relationship.manage")

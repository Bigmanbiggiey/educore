"""API views for `parents` — docs/api-design.md. A Parent always sees only
their own profile, regardless of what broader permission they might also
hold — same fail-closed object-scope pattern `students.StudentViewSet` uses
for the Student role (docs/permissions.md §3).
"""

from api.viewsets import TenantScopedModelViewSet
from apps.parents.models import ParentProfile
from apps.parents.serializers import ParentProfileSerializer
from apps.permissions.permissions import HasPermission, IsInstitutionMember
from apps.permissions.selectors import get_membership_access


class ParentProfileViewSet(TenantScopedModelViewSet):
    queryset_model = ParentProfile
    serializer_class = ParentProfileSerializer

    def get_permissions(self):
        return [IsInstitutionMember(), HasPermission("parents.parent_profile.manage")()]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.get_base_queryset()
        access = get_membership_access(self.request.user, self.request.institution)
        if "Parent" in access.role_names:
            return self.get_base_queryset().filter(user_id=self.request.user.id)
        return self.get_base_queryset()

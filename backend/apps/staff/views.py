"""API views for `staff` — docs/api-design.md. No object-scope layer here
(unlike `students`) — docs/permissions.md doesn't call out a "staff can
only see their own profile" restriction the way it does for Parent/Student,
so none is invented; access is governed by the permission check alone.
"""

from api.viewsets import TenantScopedModelViewSet
from apps.permissions.permissions import HasPermission, IsInstitutionMember
from apps.staff.models import StaffProfile
from apps.staff.serializers import StaffProfileSerializer


class StaffProfileViewSet(TenantScopedModelViewSet):
    queryset_model = StaffProfile
    serializer_class = StaffProfileSerializer

    def get_permissions(self):
        return [IsInstitutionMember(), HasPermission("staff.staff_profile.manage")()]

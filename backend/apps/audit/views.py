"""API views for `audit` — docs/permissions.md §7's "queryable fact": the
one way a System Admin (or anyone auditing the platform) reviews what
happened, including every break-glass session. Read-only, gated
`IsPlatformStaff` — `AuditLog` isn't tenant-scoped, so `IsInstitutionMember`
makes no sense here, and this data is platform-level by nature (an
institution's own admin cannot see it — audit trail integrity depends on
that).
"""

from rest_framework import mixins, viewsets

from apps.audit.filters import AuditLogFilterSet
from apps.audit.models import AuditLog
from apps.audit.serializers import AuditLogSerializer
from apps.core.permissions import IsPlatformStaff


class AuditLogViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsPlatformStaff]
    serializer_class = AuditLogSerializer
    filterset_class = AuditLogFilterSet
    queryset = AuditLog.objects.all()

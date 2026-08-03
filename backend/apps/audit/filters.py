"""Explicit filter whitelist for `audit.AuditLog` — same hand-declared
convention every other app's FilterSet uses (see `library.filters`'s
module docstring for the full `manage.py spectacular` auto-derivation
hazard this avoids).
"""

import django_filters

from apps.audit.models import AuditLog


class AuditLogFilterSet(django_filters.FilterSet):
    institution = django_filters.UUIDFilter(field_name="institution_id")
    actor = django_filters.UUIDFilter(field_name="actor_id")
    action = django_filters.CharFilter(field_name="action", lookup_expr="icontains")

    class Meta:
        model = AuditLog
        fields = ["institution", "actor", "action"]

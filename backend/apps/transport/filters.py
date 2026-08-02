"""Explicit filter whitelist for `transport.TransportAssignment` —
docs/api-design.md §6: hand-declared, not auto-derived from `Meta.fields`
(see `attendance.filters`'s module docstring for the full explanation this
project reuses everywhere).
"""

import django_filters

from apps.transport.models import TransportAssignment


class TransportAssignmentFilterSet(django_filters.FilterSet):
    student_id = django_filters.UUIDFilter(field_name="student_id")
    route = django_filters.UUIDFilter(field_name="route_id")

    class Meta:
        model = TransportAssignment
        fields = ["student_id", "route"]

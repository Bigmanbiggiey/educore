"""Explicit filter whitelist for `hostel.BedAllocation` — docs/api-design.md
§6: hand-declared, not auto-derived from `Meta.fields` (see
`attendance.filters`'s module docstring for the full explanation this
project reuses everywhere).
"""

import django_filters

from apps.hostel.models import BedAllocation


class BedAllocationFilterSet(django_filters.FilterSet):
    student_id = django_filters.UUIDFilter(field_name="student_id")
    term_id = django_filters.UUIDFilter(field_name="term_id")
    room = django_filters.UUIDFilter(field_name="room_id")

    class Meta:
        model = BedAllocation
        fields = ["student_id", "term_id", "room"]

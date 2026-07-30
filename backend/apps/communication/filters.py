"""Explicit filter whitelist for `communication` — docs/api-design.md §6:
never blanket/auto-derived field filtering (`filterset_fields`). Same
reasoning as `attendance.filters.AttendanceRecordFilterSet`'s docstring.
"""

import django_filters

from apps.communication.models import Announcement


class AnnouncementFilterSet(django_filters.FilterSet):
    kind = django_filters.ChoiceFilter(field_name="kind", choices=Announcement.Kind.choices)
    status = django_filters.ChoiceFilter(field_name="status", choices=Announcement.Status.choices)

    class Meta:
        model = Announcement
        fields = ["kind", "status"]

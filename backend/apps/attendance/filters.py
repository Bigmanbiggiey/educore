"""Explicit filter whitelist for `attendance` — docs/api-design.md §6: never
blanket/auto-derived field filtering. Filters are hand-declared, not built
from `Meta.fields`'s automatic field-type resolution — that path calls
`model_field.model._default_manager` during `manage.py spectacular`'s
schema generation, before any tenant is bound (the same issue
`classes_streams`'s views.py documents and avoids by skipping
`filterset_fields` entirely; this is the "correct way to add filtering
later" it points to).
"""

import django_filters

from apps.attendance.models import AttendanceRecord


class AttendanceRecordFilterSet(django_filters.FilterSet):
    date = django_filters.DateFilter(field_name="date")
    subject_type = django_filters.ChoiceFilter(
        field_name="subject_type", choices=AttendanceRecord.SubjectType.choices
    )
    target_id = django_filters.UUIDFilter(field_name="target_id")

    class Meta:
        model = AttendanceRecord
        fields = ["date", "subject_type", "target_id"]

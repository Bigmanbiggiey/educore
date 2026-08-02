"""Explicit filter whitelist shared by `analytics`'s three rollup list
endpoints — docs/api-design.md §6: hand-declared, not auto-derived from
`Meta.fields` (see `attendance.filters`'s module docstring for the full
explanation this project reuses everywhere). Each `FilterSet` repeats the
same two fields rather than sharing a mixin base — django-filter's
`FilterSetMetaclass` only reliably collects declared filters from the
class body it's defining, not from an arbitrary non-`FilterSet` mixin, so
repeating here is the safe, proven-elsewhere shape (no `FilterSet` in this
codebase shares filters via inheritance).
"""

import django_filters

from apps.analytics.models import AttendanceRateSnapshot, FeeCollectionSnapshot, MeanGradeRollup


class AttendanceRateSnapshotFilterSet(django_filters.FilterSet):
    class_grade_id = django_filters.UUIDFilter(field_name="class_grade_id")
    term_id = django_filters.UUIDFilter(field_name="term_id")

    class Meta:
        model = AttendanceRateSnapshot
        fields = ["class_grade_id", "term_id"]


class FeeCollectionSnapshotFilterSet(django_filters.FilterSet):
    class_grade_id = django_filters.UUIDFilter(field_name="class_grade_id")
    term_id = django_filters.UUIDFilter(field_name="term_id")

    class Meta:
        model = FeeCollectionSnapshot
        fields = ["class_grade_id", "term_id"]


class MeanGradeRollupFilterSet(django_filters.FilterSet):
    class_grade_id = django_filters.UUIDFilter(field_name="class_grade_id")
    term_id = django_filters.UUIDFilter(field_name="term_id")

    class Meta:
        model = MeanGradeRollup
        fields = ["class_grade_id", "term_id"]

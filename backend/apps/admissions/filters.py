"""Explicit filter whitelist for `admissions` — docs/api-design.md §6, same
hand-declared approach as `attendance.filters` (safe against the
auto-derivation crash `classes_streams`'s views.py documents).
"""

import django_filters

from apps.admissions.models import Application


class ApplicationFilterSet(django_filters.FilterSet):
    stage = django_filters.ChoiceFilter(field_name="stage", choices=Application.Stage.choices)
    term_applying_for_id = django_filters.UUIDFilter(field_name="term_applying_for_id")

    class Meta:
        model = Application
        fields = ["stage", "term_applying_for_id"]

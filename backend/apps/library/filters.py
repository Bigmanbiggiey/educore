"""Explicit filter whitelist for `library.Loan` — docs/api-design.md §6:
hand-declared, not auto-derived from `Meta.fields` (django-filter's
auto-derivation calls `model_field.model._default_manager` during
`manage.py spectacular`'s schema generation, outside any bound tenant —
see `attendance.filters`'s module docstring for the full explanation this
project reuses everywhere).
"""

import django_filters

from apps.library.models import BorrowerType, Loan


class LoanFilterSet(django_filters.FilterSet):
    borrower_type = django_filters.ChoiceFilter(
        field_name="borrower_type", choices=BorrowerType.choices
    )
    borrower_id = django_filters.UUIDFilter(field_name="borrower_id")
    returned = django_filters.BooleanFilter(field_name="returned_at", method="filter_returned")

    class Meta:
        model = Loan
        fields = ["borrower_type", "borrower_id"]

    def filter_returned(self, queryset, name, value):
        return queryset.filter(returned_at__isnull=not value)

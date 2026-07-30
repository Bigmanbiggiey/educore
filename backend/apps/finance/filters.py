"""Explicit filter whitelists for `finance` — docs/api-design.md §6: never
blanket/auto-derived field filtering (`filterset_fields`). Hand-declared,
same reasoning as `attendance.filters.AttendanceRecordFilterSet`'s
docstring — auto-derivation crashes `manage.py spectacular`'s schema
generation, which runs with no tenant bound.
"""

import django_filters

from apps.finance.models import Invoice, Payment


class InvoiceFilterSet(django_filters.FilterSet):
    student = django_filters.UUIDFilter(field_name="student_id")
    term = django_filters.UUIDFilter(field_name="term_id")
    status = django_filters.ChoiceFilter(field_name="status", choices=Invoice.Status.choices)

    class Meta:
        model = Invoice
        fields = ["student", "term", "status"]


class PaymentFilterSet(django_filters.FilterSet):
    invoice = django_filters.UUIDFilter(field_name="invoice_id")
    method = django_filters.ChoiceFilter(field_name="method", choices=Payment.Method.choices)

    class Meta:
        model = Payment
        fields = ["invoice", "method"]

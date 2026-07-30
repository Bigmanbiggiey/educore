"""Explicit filter whitelists for `finance` — docs/api-design.md §6: never
blanket/auto-derived field filtering (`filterset_fields`). Hand-declared,
same reasoning as `attendance.filters.AttendanceRecordFilterSet`'s
docstring — auto-derivation crashes `manage.py spectacular`'s schema
generation, which runs with no tenant bound.
"""

import django_filters

from apps.finance.models import ExpenseRecord, Invoice, Payment, Payroll


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


class PayrollFilterSet(django_filters.FilterSet):
    staff = django_filters.UUIDFilter(field_name="staff_id")
    period = django_filters.DateFilter(field_name="period")

    class Meta:
        model = Payroll
        fields = ["staff", "period"]


class ExpenseRecordFilterSet(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name="category")
    incurred_at = django_filters.DateFilter(field_name="incurred_at")

    class Meta:
        model = ExpenseRecord
        fields = ["category", "incurred_at"]

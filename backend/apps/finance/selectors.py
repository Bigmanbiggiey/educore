"""Public read interface for `finance` — docs/modules.md.

Every selector takes `institution` explicitly and binds it via
`bind_institution`, same reasoning as every other Layer 1 app's
selectors.py (Celery-safety: nothing here relies on an ambiently-bound
tenant, e.g. a future recurring-fee-reminder task).
"""

import uuid
from decimal import Decimal

from django.db.models import Sum

from apps.core.context import bind_institution
from apps.finance.models import Invoice, Payment
from apps.institutions.models import Institution


def get_balance(
    institution: Institution, student_id: uuid.UUID, term_id: uuid.UUID | None = None
) -> Decimal:
    """`amount_due - amount_paid` across the student's invoices (cancelled
    invoices excluded — they never owed anything real)."""
    with bind_institution(institution):
        qs = Invoice.objects.filter(student_id=student_id).exclude(status=Invoice.Status.CANCELLED)
        if term_id is not None:
            qs = qs.filter(term_id=term_id)
        total_due = qs.aggregate(total=Sum("amount_due"))["total"] or Decimal("0")
        total_paid = Payment.objects.filter(invoice__in=qs).aggregate(total=Sum("amount"))[
            "total"
        ] or Decimal("0")
        return total_due - total_paid


def get_invoices_for_student(
    institution: Institution, student_id: uuid.UUID, term_id: uuid.UUID | None = None
):
    with bind_institution(institution):
        qs = Invoice.objects.filter(student_id=student_id)
        if term_id is not None:
            qs = qs.filter(term_id=term_id)
        return list(qs)


def get_payments_for_invoice(institution: Institution, invoice: Invoice):
    with bind_institution(institution):
        return list(invoice.payments.all())


def get_institution_financial_summary(institution: Institution, term_id: uuid.UUID) -> dict:
    """Basic "Financial Reports" deliverable (docs/roadmap.md Phase 4) —
    totals a Finance Officer needs day-to-day. Deeper analytics/exports
    stay out of scope here, that's `analytics`/`reports` territory later
    (Phase 8)."""
    with bind_institution(institution):
        invoices = Invoice.objects.filter(term_id=term_id).exclude(status=Invoice.Status.CANCELLED)
        total_invoiced = invoices.aggregate(total=Sum("amount_due"))["total"] or Decimal("0")
        payments = Payment.objects.filter(invoice__in=invoices)
        total_collected = payments.aggregate(total=Sum("amount"))["total"] or Decimal("0")
        by_method = {
            row["method"]: row["total"]
            for row in payments.values("method").annotate(total=Sum("amount"))
        }
        return {
            "term_id": str(term_id),
            "total_invoiced": total_invoiced,
            "total_collected": total_collected,
            "total_outstanding": total_invoiced - total_collected,
            "by_method": by_method,
        }

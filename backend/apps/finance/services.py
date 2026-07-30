"""Public write interface for `finance` — docs/modules.md.

Every write here binds `institution` for the duration of the call
(`apps.core.context.bind_institution`), same convention as every other
Layer 1 app's services.py. Multi-write functions run inside
`transaction.atomic()`, same pairing-of-writes discipline as
`classes_streams.set_current_term`/`admissions.make_offer`.

`generate_invoices_for_class` deliberately loops and calls
`Invoice.objects.create(...)` per student rather than `bulk_create` — this
is finance's highest-scrutiny requirement (docs/database.md: "every write
audited"), and `bulk_create` does not fire `post_save` signals, which
would silently skip `apps.finance.signals`' audit-log wiring for every
generated invoice. Correctness of the audit trail outweighs the bulk-insert
performance win here.
"""

import uuid
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum

from apps.core.context import bind_institution
from apps.finance.models import (
    FeeStructure,
    InstallmentPlan,
    Invoice,
    Payment,
    Receipt,
    Scholarship,
)
from apps.institutions.models import Institution


def create_fee_structure(
    *,
    institution: Institution,
    class_grade_id: uuid.UUID,
    term_id: uuid.UUID,
    name: str,
    line_items: list[dict],
) -> FeeStructure:
    total_amount = sum((Decimal(str(item["amount"])) for item in line_items), Decimal("0"))
    with bind_institution(institution):
        return FeeStructure.objects.create(
            institution_id=institution.id,
            class_grade_id=class_grade_id,
            term_id=term_id,
            name=name,
            line_items=line_items,
            total_amount=total_amount,
        )


@transaction.atomic
def generate_invoices_for_class(
    *, institution: Institution, fee_structure: FeeStructure, student_ids: list[uuid.UUID]
) -> list[Invoice]:
    """One `Invoice` per `student_id`, reduced by any active `Scholarship`
    for that student+term. `student_ids` is resolved by the caller
    (`views.py`, via `students.selectors.get_active_roster`) — `finance`'s
    own services/models stay free of a real `students` import; only
    object-scoping in `views.py` needs one, same shape `academics.views`
    already established for the same reason."""
    with bind_institution(institution):
        scholarships = {
            s.student_id: s
            for s in Scholarship.objects.filter(
                term_id=fee_structure.term_id, student_id__in=student_ids
            )
        }
        invoices = []
        for student_id in student_ids:
            amount_due = fee_structure.total_amount
            scholarship = scholarships.get(student_id)
            if scholarship is not None:
                if scholarship.is_percent:
                    amount_due -= amount_due * scholarship.amount_or_percent / Decimal("100")
                else:
                    amount_due -= scholarship.amount_or_percent
                amount_due = max(amount_due, Decimal("0"))
            invoices.append(
                Invoice.objects.create(
                    institution_id=institution.id,
                    student_id=student_id,
                    term_id=fee_structure.term_id,
                    fee_structure_id=fee_structure.id,
                    amount_due=amount_due,
                )
            )
    return invoices


def set_installment_plan(
    *, institution: Institution, invoice: Invoice, num_installments: int, schedule: list[dict]
) -> InstallmentPlan:
    with bind_institution(institution):
        return InstallmentPlan.objects.create(
            institution_id=institution.id,
            invoice=invoice,
            num_installments=num_installments,
            schedule=schedule,
        )


def _next_receipt_number(institution: Institution) -> str:
    # Sequential per institution. A concurrent race could in theory produce
    # the same count-derived number for two payments landing in the same
    # instant — the unique constraint on Receipt.receipt_number fails that
    # write loudly (IntegrityError) rather than silently issuing a
    # duplicate receipt, which is the correct failure mode for this data.
    count = Receipt.objects.count()
    return f"RCPT-{institution.slug.upper()}-{count + 1:06d}"


@transaction.atomic
def record_payment(
    *,
    institution: Institution,
    invoice: Invoice,
    amount: Decimal,
    method: str,
    reference: str,
    paid_at,
    recorded_by_id: uuid.UUID | None,
) -> Payment:
    with bind_institution(institution):
        payment = Payment.objects.create(
            institution_id=institution.id,
            invoice=invoice,
            amount=amount,
            method=method,
            reference=reference,
            paid_at=paid_at,
            recorded_by_id=recorded_by_id,
        )
        total_paid = invoice.payments.aggregate(total=Sum("amount"))["total"] or Decimal("0")
        if total_paid >= invoice.amount_due:
            invoice.status = Invoice.Status.PAID
        elif total_paid > 0:
            invoice.status = Invoice.Status.PARTIAL
        invoice.save(update_fields=["status", "updated_at"])
        Receipt.objects.create(
            institution_id=institution.id,
            payment=payment,
            receipt_number=_next_receipt_number(institution),
        )
    return payment


def grant_scholarship(
    *,
    institution: Institution,
    student_id: uuid.UUID,
    term_id: uuid.UUID,
    amount_or_percent: Decimal,
    is_percent: bool,
    funded_by: str = "",
) -> Scholarship:
    with bind_institution(institution):
        return Scholarship.objects.create(
            institution_id=institution.id,
            student_id=student_id,
            term_id=term_id,
            amount_or_percent=amount_or_percent,
            is_percent=is_percent,
            funded_by=funded_by,
        )

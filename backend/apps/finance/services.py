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

import datetime
import secrets
import uuid
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import Sum

from apps.core.context import bind_institution
from apps.finance.models import (
    ExpenseRecord,
    FeeStructure,
    InstallmentPlan,
    Invoice,
    MpesaSTKPushRequest,
    Payment,
    Payroll,
    Receipt,
    Scholarship,
)
from apps.finance.mpesa_backends import MpesaGatewayError, get_mpesa_backend
from apps.finance.selectors import get_invoice_balance
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


def _finalize_payment(*, institution: Institution, invoice: Invoice, payment: Payment) -> None:
    """Recomputes `Invoice.status` from `sum(payments)` vs `amount_due` and
    creates the matching `Receipt` — shared by the manual-entry path
    (`record_payment`) and the M-Pesa confirmation path
    (`handle_mpesa_callback` below), so the two don't duplicate this logic.
    Must run with `institution` already bound by the caller."""
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
        _finalize_payment(institution=institution, invoice=invoice, payment=payment)
    return payment


@transaction.atomic
def initiate_mpesa_stk_push(
    *,
    institution: Institution,
    invoice: Invoice,
    phone_number: str,
    amount: Decimal | None,
    initiated_by_id: uuid.UUID | None,
) -> MpesaSTKPushRequest:
    """Creates the pending `MpesaSTKPushRequest` row first (so its `id`
    exists to build the callback URL embedding it), then calls the
    configured gateway backend. `amount` defaults to the invoice's full
    remaining balance when omitted; either way it's capped at that
    balance — an STK Push can never be raised for more than what's
    actually still owed on this invoice, regardless of which actor
    (Finance Officer or self-service Parent) initiated it."""
    with bind_institution(institution):
        remaining = get_invoice_balance(institution, invoice)
        if amount is None:
            amount = remaining
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")
        if amount > remaining:
            raise ValueError(f"Amount exceeds the invoice's remaining balance of {remaining}.")

        stk_request = MpesaSTKPushRequest.objects.create(
            institution_id=institution.id,
            invoice=invoice,
            phone_number=phone_number,
            amount=amount,
            verification_token=secrets.token_urlsafe(32),
            initiated_by_id=initiated_by_id,
        )
        callback_url = (
            f"{settings.MPESA_CALLBACK_BASE_URL}/api/v1/webhooks/mpesa/callback/"
            f"{institution.id}/{stk_request.id}/{stk_request.verification_token}/"
        )
        try:
            result = get_mpesa_backend().initiate_stk_push(
                phone_number=phone_number,
                amount=amount,
                account_reference=str(invoice.id),
                transaction_desc=f"Invoice {invoice.id}",
                callback_url=callback_url,
            )
        except MpesaGatewayError as exc:
            stk_request.status = MpesaSTKPushRequest.Status.FAILED
            stk_request.result_desc = str(exc)
            stk_request.save(update_fields=["status", "result_desc", "updated_at"])
            raise ValueError(str(exc)) from exc

        stk_request.merchant_request_id = result["merchant_request_id"]
        stk_request.checkout_request_id = result["checkout_request_id"]
        stk_request.save(update_fields=["merchant_request_id", "checkout_request_id", "updated_at"])
    return stk_request


@transaction.atomic
def handle_mpesa_callback(
    *,
    institution: Institution,
    stk_request: MpesaSTKPushRequest,
    result_code: int,
    result_desc: str,
    callback_metadata: dict | None,
) -> MpesaSTKPushRequest:
    """Idempotent: no-ops if `stk_request` is no longer `PENDING` — Safaricom
    retries callbacks on timeout, so a second delivery for an
    already-resolved request must be a no-op, never reprocessed
    (docs/api-design.md §11). On success, `Payment` is
    `get_or_create`-keyed on `mpesa_transaction_id` as the second,
    belt-and-braces layer of that same idempotency guarantee."""
    with bind_institution(institution):
        if stk_request.status != MpesaSTKPushRequest.Status.PENDING:
            return stk_request

        stk_request.result_code = result_code
        stk_request.result_desc = result_desc

        if result_code == 0:
            callback_metadata = callback_metadata or {}
            payment, created = Payment.objects.get_or_create(
                mpesa_transaction_id=callback_metadata["mpesa_receipt_number"],
                defaults={
                    "institution_id": institution.id,
                    "invoice": stk_request.invoice,
                    "amount": callback_metadata["amount"],
                    "method": Payment.Method.MPESA,
                    "reference": callback_metadata["mpesa_receipt_number"],
                    "paid_at": callback_metadata["transaction_date"],
                    "recorded_by_id": stk_request.initiated_by_id,
                },
            )
            if created:
                _finalize_payment(
                    institution=institution, invoice=stk_request.invoice, payment=payment
                )
            stk_request.payment = payment
            stk_request.status = MpesaSTKPushRequest.Status.SUCCESS
        elif result_code == 1032:
            # Safaricom's code for "request cancelled by user".
            stk_request.status = MpesaSTKPushRequest.Status.CANCELLED
        else:
            stk_request.status = MpesaSTKPushRequest.Status.FAILED

        stk_request.save(
            update_fields=["status", "result_code", "result_desc", "payment", "updated_at"]
        )
    return stk_request


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


def create_payroll_record(
    *,
    institution: Institution,
    staff_id: uuid.UUID,
    period: datetime.date,
    gross: Decimal,
    deductions: list[dict],
    paid_at,
) -> Payroll:
    """`net` is computed here, never entered redundantly by the caller —
    same "computed, not redundant" precedent as
    `create_fee_structure`'s `total_amount`. Deliberately not clamped at
    zero: deductions can legitimately exceed gross (e.g. a loan recovery
    month), and `net` should reflect that truthfully."""
    total_deductions = sum((Decimal(str(item["amount"])) for item in deductions), Decimal("0"))
    with bind_institution(institution):
        return Payroll.objects.create(
            institution_id=institution.id,
            staff_id=staff_id,
            period=period,
            gross=gross,
            deductions=deductions,
            net=gross - total_deductions,
            paid_at=paid_at,
        )


def record_expense(
    *,
    institution: Institution,
    category: str,
    amount: Decimal,
    incurred_at: datetime.date,
    approved_by_id: uuid.UUID | None,
) -> ExpenseRecord:
    """`docs/database.md` lists `ExpenseRecord` as one flat row, not a
    proposal/approval-stage pair — same "don't invent a stage history the
    docs don't specify" call already made for `Scholarship`.
    `approved_by_id` is server-injected from `request.user.id` by the
    caller (`views.py`), never client-supplied: only someone holding
    `finance.expense_record.manage` can write one at all, so their write
    *is* the approval — same pattern as `Payment.recorded_by_id`."""
    with bind_institution(institution):
        return ExpenseRecord.objects.create(
            institution_id=institution.id,
            category=category,
            amount=amount,
            incurred_at=incurred_at,
            approved_by_id=approved_by_id,
        )

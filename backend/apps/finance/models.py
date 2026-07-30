"""Layer 1 models — docs/database.md §"Finance (the highest-scrutiny module
— every write audited)", docs/modules.md (`finance`).

Phase 4 Stage 1 scope: core billing and manual payments (cash/bank, plus a
manually-reconciled M-Pesa reference). Stage 2 adds the live M-Pesa STK
Push/callback integration: `MpesaSTKPushRequest` (the pending-request
lifecycle — a push can be sent and never confirmed) and
`Payment.mpesa_transaction_id` (what the callback upserts on, per
docs/api-design.md §11). `Payroll`/`ExpenseRecord` remain a later stage
(docs/roadmap.md).

`Invoice`/`Payment` use `TenantScopedSoftDeleteModel` — both are named
explicitly in `apps.core.models.TenantScopedSoftDeleteModel`'s own
docstring as soft-deletable. `FeeStructure`/`InstallmentPlan`/
`Scholarship`/`Receipt` are plain `TenantScopedModel` (hard-delete).

Every cross-app reference (`class_grade_id`, `term_id`, `student_id`,
`recorded_by_id`) is a plain `UUIDField`, never a live FK — same convention
as every other Layer 1 app's cross-app references (docs/multitenancy.md
§1). `invoice`/`payment` FKs below are intra-app, so they stay real
ForeignKeys.
"""

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from apps.core.models import TenantScopedModel, TenantScopedSoftDeleteModel


class FeeStructure(TenantScopedModel):
    class_grade_id = models.UUIDField()
    term_id = models.UUIDField()
    name = models.CharField(max_length=100)
    # Unstructured list of {"description": ..., "amount": ...} — too
    # institution-specific for a fixed schema, same call as
    # academics.GradingScale.levels/admissions.Application.applicant_details.
    # `encoder=DjangoJSONEncoder` — plain json.dumps can't serialize the
    # Decimal amounts this list carries; DjangoJSONEncoder writes them as
    # JSON strings (money-as-string is fine for this informational list —
    # the real, arithmetic-safe total lives in `total_amount` below).
    line_items = models.JSONField(default=list, blank=True, encoder=DjangoJSONEncoder)
    # Computed by services.create_fee_structure as the sum of
    # line_items[].amount — never entered redundantly by the caller.
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ["-created_at"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "class_grade_id", "term_id", "name"],
            name="feestructure_unique_per_class_term_name",
        ),
    ]

    def __str__(self) -> str:
        return f"{self.name} — {self.total_amount}"


class Invoice(TenantScopedSoftDeleteModel):
    class Status(models.TextChoices):
        UNPAID = "unpaid", "Unpaid"
        PARTIAL = "partial", "Partial"
        PAID = "paid", "Paid"
        OVERDUE = "overdue", "Overdue"
        CANCELLED = "cancelled", "Cancelled"

    student_id = models.UUIDField()
    term_id = models.UUIDField()
    # Nullable — an invoice can be raised ad hoc, with no FeeStructure
    # behind it (docs/database.md's own schema shows FeeStructure as
    # optional context for an Invoice, not a required parent).
    fee_structure_id = models.UUIDField(null=True, blank=True)
    amount_due = models.DecimalField(max_digits=12, decimal_places=2)
    # Recomputed by services.record_payment from sum(payments) vs
    # amount_due — never set directly by a client.
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UNPAID)

    class Meta:
        ordering = ["-created_at"]

    Meta.constraints = [
        models.CheckConstraint(
            condition=models.Q(status__in=Status.values), name="invoice_valid_status"
        ),
        models.CheckConstraint(
            condition=models.Q(amount_due__gte=0), name="invoice_amount_due_non_negative"
        ),
    ]

    # (institution_id, term_id) and (institution_id, student_id) are the
    # hot finance lookups — docs/database.md's own indexing guidance.
    Meta.indexes = [
        models.Index(fields=["institution_id", "term_id"]),
        models.Index(fields=["institution_id", "student_id"]),
    ]

    def __str__(self) -> str:
        return f"Invoice {self.id} — student {self.student_id} — {self.get_status_display()}"


class InstallmentPlan(TenantScopedModel):
    """Plain FK to `Invoice`, not `OneToOne` — same "revise without
    destroying history" reasoning as `admissions.Offer`'s FK-not-OneToOne
    precedent: a revised plan is a new row, `services.set_installment_plan`
    doesn't need to mutate or delete the previous one."""

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="installment_plans")
    num_installments = models.PositiveSmallIntegerField()
    # list of {"due_date": ..., "amount": ...} — DjangoJSONEncoder, same
    # reasoning as FeeStructure.line_items (dates and Decimals both need it).
    schedule = models.JSONField(default=list, blank=True, encoder=DjangoJSONEncoder)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Installment plan — invoice {self.invoice_id} ({self.num_installments}x)"


class Payment(TenantScopedSoftDeleteModel):
    class Method(models.TextChoices):
        MPESA = "mpesa", "M-Pesa"
        CASH = "cash", "Cash"
        BANK = "bank", "Bank"

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    # "mpesa" covers both a manually-entered reconciliation reference (a
    # Finance Officer typing in a till/paybill confirmation code, Stage 1)
    # and a confirmed STK Push (Stage 2, `mpesa_transaction_id` set).
    method = models.CharField(max_length=10, choices=Method.choices)
    reference = models.CharField(max_length=100, blank=True, default="")
    # M-Pesa's own `MpesaReceiptNumber` from a confirmed STK Push callback —
    # what `services.handle_mpesa_callback` upserts a `Payment` on
    # (docs/api-design.md §11: "a duplicate callback is a no-op 200, never
    # a duplicate payment"). Null for Stage 1 manual entries.
    mpesa_transaction_id = models.CharField(max_length=30, null=True, blank=True)
    paid_at = models.DateTimeField()
    # Server-injected from request.user.id in services.record_payment,
    # never client-supplied — same pattern as
    # curriculum_british.set_predicted_grade's set_by. Nullable: a
    # system/Celery-initiated payment (e.g. an M-Pesa webhook) has no human
    # actor, same reasoning as audit.AuditLog.actor.
    recorded_by_id = models.UUIDField(null=True, blank=True)

    class Meta:
        ordering = ["-paid_at"]

    Meta.constraints = [
        models.CheckConstraint(condition=models.Q(amount__gt=0), name="payment_amount_positive"),
        models.UniqueConstraint(
            fields=["institution_id", "mpesa_transaction_id"],
            condition=models.Q(mpesa_transaction_id__isnull=False),
            name="payment_unique_mpesa_transaction_id",
        ),
    ]

    Meta.indexes = [
        models.Index(fields=["institution_id", "invoice"]),
    ]

    def __str__(self) -> str:
        return f"Payment {self.amount} ({self.get_method_display()}) — invoice {self.invoice_id}"


class Receipt(TenantScopedModel):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name="receipt")
    receipt_number = models.CharField(max_length=30)
    # PDF rendering belongs to the not-yet-built `documents`/`reports` apps
    # (Layer 1/3) — deliberately left blank for now rather than guessed at,
    # same "don't build against a dependency that doesn't exist yet" call
    # `staff` made for its deferred selectors in Phase 2.
    pdf_document = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["-created_at"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "receipt_number"],
            name="receipt_unique_number_per_institution",
        ),
    ]

    def __str__(self) -> str:
        return f"Receipt {self.receipt_number}"


class MpesaSTKPushRequest(TenantScopedModel):
    """The pending-request lifecycle for a Safaricom STK Push — a push can
    be sent and never confirmed (customer cancels, wrong PIN, timeout), so
    this is deliberately separate from `Payment`, which represents a
    confirmed, "it happened" record — same "current value + history table"
    split as `admissions.Application`/`ApplicationStage`. A `Payment` row
    is only ever created once `services.handle_mpesa_callback` sees a
    successful result, never at initiation time.

    `verification_token` is embedded in the callback URL Safaricom is told
    to call (`services.initiate_mpesa_stk_push`) and re-checked via
    `hmac.compare_digest` in `webhooks.MpesaCallbackView` before anything
    else runs — a second, DB-independent check alongside the source-IP
    allowlist, since Safaricom's STK Push callback carries no cryptographic
    payload signature of its own (docs/api-design.md §11's "signature"
    requirement, met the only way actually available here).
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name="mpesa_stk_requests"
    )
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    merchant_request_id = models.CharField(max_length=50, blank=True, default="")
    checkout_request_id = models.CharField(max_length=50, blank=True, default="")
    verification_token = models.CharField(max_length=64)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    result_code = models.IntegerField(null=True, blank=True)
    result_desc = models.CharField(max_length=255, blank=True, default="")
    # Set once a confirmed callback creates the resulting Payment.
    payment = models.OneToOneField(
        Payment, on_delete=models.SET_NULL, null=True, blank=True, related_name="mpesa_stk_request"
    )
    # The acting user — a Finance Officer (on behalf of someone) or a
    # self-service Parent (only ever their own phone number, never
    # client-supplied — enforced in views.py, not here).
    initiated_by_id = models.UUIDField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    Meta.constraints = [
        models.CheckConstraint(
            condition=models.Q(amount__gt=0), name="mpesastkpush_amount_positive"
        ),
        models.CheckConstraint(
            condition=models.Q(status__in=Status.values), name="mpesastkpush_valid_status"
        ),
    ]

    Meta.indexes = [
        models.Index(fields=["institution_id", "checkout_request_id"]),
    ]

    def __str__(self) -> str:
        return f"STK Push — invoice {self.invoice_id} — {self.get_status_display()}"


class Scholarship(TenantScopedModel):
    student_id = models.UUIDField()
    term_id = models.UUIDField()
    # docs name this one conceptual field "amount_or_percent" — represented
    # as a value + an is_percent flag rather than a string typed two ways.
    amount_or_percent = models.DecimalField(max_digits=12, decimal_places=2)
    is_percent = models.BooleanField(default=False)
    funded_by = models.CharField(max_length=150, blank=True, default="")

    class Meta:
        ordering = ["-created_at"]

    Meta.constraints = [
        models.CheckConstraint(
            condition=models.Q(amount_or_percent__gt=0), name="scholarship_amount_positive"
        ),
    ]

    def __str__(self) -> str:
        return f"Scholarship — student {self.student_id} — {self.amount_or_percent}"


class Payroll(TenantScopedModel):
    """Stage 3 (docs/roadmap.md). `staff_id` is a plain cross-app UUID to
    `staff.StaffProfile` — same convention as every other Layer 1
    cross-app reference; `finance` needs no live import of `apps.staff`
    for this (no object-scoping calls for one, unlike the `students` edge
    `InvoiceViewSet` has).
    """

    staff_id = models.UUIDField()
    # First day of the pay-period month (e.g. 2026-01-01 for January
    # 2026) — docs/database.md's "period" field, read as a single date
    # rather than a start/end pair for simplicity, same "pick the
    # simplest concrete reading" precedent as curriculum_844's exam-type
    # discriminator.
    period = models.DateField()
    gross = models.DecimalField(max_digits=12, decimal_places=2)
    # list of {"description": ..., "amount": ...} — DjangoJSONEncoder,
    # same reasoning as FeeStructure.line_items.
    deductions = models.JSONField(default=list, blank=True, encoder=DjangoJSONEncoder)
    # Computed by services.create_payroll_record as gross minus the sum of
    # deductions[].amount — never entered redundantly by the caller.
    # Deliberately unconstrained to be non-negative: deductions can
    # legitimately exceed gross (e.g. a loan recovery month), and net
    # should reflect that truthfully rather than being clamped or
    # rejected.
    net = models.DecimalField(max_digits=12, decimal_places=2)
    paid_at = models.DateTimeField()

    class Meta:
        ordering = ["-period"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "staff_id", "period"],
            name="payroll_unique_per_staff_period",
        ),
        models.CheckConstraint(condition=models.Q(gross__gt=0), name="payroll_gross_positive"),
    ]

    def __str__(self) -> str:
        return f"Payroll — staff {self.staff_id} — {self.period}"


class ExpenseRecord(TenantScopedModel):
    """docs/database.md lists this as one flat row, not a
    proposal/approval-stage pair — same "don't invent a stage history the
    docs don't specify" call already made for `Scholarship`.
    `approved_by_id` is server-injected from `request.user.id` at creation
    (`services.record_expense`), never client-supplied: only someone
    holding `finance.expense_record.manage` can write one at all, so their
    write *is* the approval — same pattern as `Payment.recorded_by_id`.
    """

    # Free text, not an enum — unlike Payment.method (an explicit
    # doc-given list), no category list is given, so none is invented.
    category = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    incurred_at = models.DateField()
    approved_by_id = models.UUIDField(null=True, blank=True)

    class Meta:
        ordering = ["-incurred_at"]

    Meta.constraints = [
        models.CheckConstraint(
            condition=models.Q(amount__gt=0), name="expenserecord_amount_positive"
        ),
    ]

    def __str__(self) -> str:
        return f"Expense — {self.category} — {self.amount}"

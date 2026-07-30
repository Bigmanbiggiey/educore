import uuid
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.core.context import bind_institution
from apps.finance.models import ExpenseRecord, Invoice, MpesaSTKPushRequest, Payment, Scholarship
from apps.finance.services import (
    create_fee_structure,
    create_payroll_record,
    generate_invoices_for_class,
    grant_scholarship,
    handle_mpesa_callback,
    initiate_mpesa_stk_push,
    record_expense,
    record_payment,
    set_installment_plan,
)
from apps.institutions.models import Institution


class FinanceServiceTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")


class CreateFeeStructureTests(FinanceServiceTestCase):
    def test_computes_total_amount_from_line_items(self):
        fee_structure = create_fee_structure(
            institution=self.institution,
            class_grade_id=uuid.uuid4(),
            term_id=uuid.uuid4(),
            name="Tuition",
            line_items=[
                {"description": "Tuition", "amount": "800.00"},
                {"description": "Activity fee", "amount": "200.00"},
            ],
        )

        self.assertEqual(fee_structure.total_amount, Decimal("1000.00"))


class GenerateInvoicesForClassTests(FinanceServiceTestCase):
    def _fee_structure(self, total_amount="1000.00"):
        return create_fee_structure(
            institution=self.institution,
            class_grade_id=uuid.uuid4(),
            term_id=uuid.uuid4(),
            name="Tuition",
            line_items=[{"description": "Tuition", "amount": total_amount}],
        )

    def test_creates_one_invoice_per_student(self):
        fee_structure = self._fee_structure()
        student_ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]

        invoices = generate_invoices_for_class(
            institution=self.institution, fee_structure=fee_structure, student_ids=student_ids
        )

        self.assertEqual(len(invoices), 3)
        with bind_institution(self.institution):
            self.assertEqual(Invoice.objects.count(), 3)
            for invoice in invoices:
                self.assertEqual(invoice.amount_due, Decimal("1000.00"))
                self.assertEqual(invoice.term_id, fee_structure.term_id)

    def test_flat_scholarship_reduces_amount_due(self):
        fee_structure = self._fee_structure()
        student_id = uuid.uuid4()
        with bind_institution(self.institution):
            Scholarship.objects.create(
                institution_id=self.institution.id,
                student_id=student_id,
                term_id=fee_structure.term_id,
                amount_or_percent=Decimal("300.00"),
                is_percent=False,
            )

        invoices = generate_invoices_for_class(
            institution=self.institution, fee_structure=fee_structure, student_ids=[student_id]
        )

        self.assertEqual(invoices[0].amount_due, Decimal("700.00"))

    def test_percent_scholarship_reduces_amount_due(self):
        fee_structure = self._fee_structure()
        student_id = uuid.uuid4()
        with bind_institution(self.institution):
            Scholarship.objects.create(
                institution_id=self.institution.id,
                student_id=student_id,
                term_id=fee_structure.term_id,
                amount_or_percent=Decimal("50"),
                is_percent=True,
            )

        invoices = generate_invoices_for_class(
            institution=self.institution, fee_structure=fee_structure, student_ids=[student_id]
        )

        self.assertEqual(invoices[0].amount_due, Decimal("500.00"))

    def test_scholarship_never_pushes_amount_due_negative(self):
        fee_structure = self._fee_structure("100.00")
        student_id = uuid.uuid4()
        with bind_institution(self.institution):
            Scholarship.objects.create(
                institution_id=self.institution.id,
                student_id=student_id,
                term_id=fee_structure.term_id,
                amount_or_percent=Decimal("500.00"),
                is_percent=False,
            )

        invoices = generate_invoices_for_class(
            institution=self.institution, fee_structure=fee_structure, student_ids=[student_id]
        )

        self.assertEqual(invoices[0].amount_due, Decimal("0"))


class RecordPaymentTests(FinanceServiceTestCase):
    def _invoice(self, amount_due="1000.00"):
        with bind_institution(self.institution):
            return Invoice.objects.create(
                institution_id=self.institution.id,
                student_id=uuid.uuid4(),
                term_id=uuid.uuid4(),
                amount_due=Decimal(amount_due),
            )

    def test_partial_payment_marks_invoice_partial(self):
        invoice = self._invoice()

        payment = record_payment(
            institution=self.institution,
            invoice=invoice,
            amount=Decimal("400.00"),
            method=Payment.Method.CASH,
            reference="",
            paid_at=timezone.now(),
            recorded_by_id=None,
        )

        invoice.refresh_from_db()
        self.assertEqual(invoice.status, Invoice.Status.PARTIAL)
        with bind_institution(self.institution):
            self.assertEqual(payment.receipt.payment_id, payment.id)

    def test_full_payment_marks_invoice_paid_and_creates_a_receipt(self):
        invoice = self._invoice()

        payment = record_payment(
            institution=self.institution,
            invoice=invoice,
            amount=Decimal("1000.00"),
            method=Payment.Method.MPESA,
            reference="QGH7XXYYZZ",
            paid_at=timezone.now(),
            recorded_by_id=None,
        )

        invoice.refresh_from_db()
        self.assertEqual(invoice.status, Invoice.Status.PAID)
        with bind_institution(self.institution):
            self.assertTrue(payment.receipt.receipt_number.startswith("RCPT-"))

    def test_second_payment_completing_the_balance_marks_paid(self):
        invoice = self._invoice()
        record_payment(
            institution=self.institution,
            invoice=invoice,
            amount=Decimal("400.00"),
            method=Payment.Method.CASH,
            reference="",
            paid_at=timezone.now(),
            recorded_by_id=None,
        )

        record_payment(
            institution=self.institution,
            invoice=invoice,
            amount=Decimal("600.00"),
            method=Payment.Method.BANK,
            reference="",
            paid_at=timezone.now(),
            recorded_by_id=None,
        )

        invoice.refresh_from_db()
        self.assertEqual(invoice.status, Invoice.Status.PAID)
        with bind_institution(self.institution):
            self.assertEqual(Payment.objects.filter(invoice=invoice).count(), 2)


class SetInstallmentPlanTests(FinanceServiceTestCase):
    def test_creates_a_plan_with_the_given_schedule(self):
        with bind_institution(self.institution):
            invoice = Invoice.objects.create(
                institution_id=self.institution.id,
                student_id=uuid.uuid4(),
                term_id=uuid.uuid4(),
                amount_due="1000.00",
            )

        plan = set_installment_plan(
            institution=self.institution,
            invoice=invoice,
            num_installments=2,
            schedule=[
                {"due_date": "2026-02-01", "amount": "500.00"},
                {"due_date": "2026-03-01", "amount": "500.00"},
            ],
        )

        self.assertEqual(plan.num_installments, 2)
        self.assertEqual(len(plan.schedule), 2)


class GrantScholarshipTests(FinanceServiceTestCase):
    def test_creates_a_scholarship(self):
        scholarship = grant_scholarship(
            institution=self.institution,
            student_id=uuid.uuid4(),
            term_id=uuid.uuid4(),
            amount_or_percent=Decimal("25"),
            is_percent=True,
            funded_by="Alumni Fund",
        )

        self.assertTrue(scholarship.is_percent)
        self.assertEqual(scholarship.funded_by, "Alumni Fund")


class InitiateMpesaStkPushTests(FinanceServiceTestCase):
    # base.py's default MPESA_GATEWAY_BACKEND is FakeMpesaGatewayBackend —
    # no network, no settings override needed here.

    def _invoice(self, amount_due="1000.00"):
        with bind_institution(self.institution):
            return Invoice.objects.create(
                institution_id=self.institution.id,
                student_id=uuid.uuid4(),
                term_id=uuid.uuid4(),
                amount_due=Decimal(amount_due),
            )

    def test_defaults_amount_to_the_full_remaining_balance(self):
        invoice = self._invoice()

        stk_request = initiate_mpesa_stk_push(
            institution=self.institution,
            invoice=invoice,
            phone_number="254712345678",
            amount=None,
            initiated_by_id=uuid.uuid4(),
        )

        self.assertEqual(stk_request.amount, Decimal("1000.00"))
        self.assertEqual(stk_request.status, MpesaSTKPushRequest.Status.PENDING)
        self.assertTrue(stk_request.checkout_request_id)

    def test_rejects_amount_exceeding_the_remaining_balance(self):
        invoice = self._invoice(amount_due="500.00")

        with self.assertRaises(ValueError):
            initiate_mpesa_stk_push(
                institution=self.institution,
                invoice=invoice,
                phone_number="254712345678",
                amount=Decimal("600.00"),
                initiated_by_id=uuid.uuid4(),
            )

    def test_rejects_a_non_positive_amount(self):
        invoice = self._invoice()

        with self.assertRaises(ValueError):
            initiate_mpesa_stk_push(
                institution=self.institution,
                invoice=invoice,
                phone_number="254712345678",
                amount=Decimal("0"),
                initiated_by_id=uuid.uuid4(),
            )

    def test_caps_at_the_remaining_balance_after_a_partial_payment(self):
        invoice = self._invoice()
        record_payment(
            institution=self.institution,
            invoice=invoice,
            amount=Decimal("400.00"),
            method=Payment.Method.CASH,
            reference="",
            paid_at=timezone.now(),
            recorded_by_id=None,
        )
        invoice.refresh_from_db()

        with self.assertRaises(ValueError):
            initiate_mpesa_stk_push(
                institution=self.institution,
                invoice=invoice,
                phone_number="254712345678",
                amount=Decimal("601.00"),
                initiated_by_id=uuid.uuid4(),
            )

        stk_request = initiate_mpesa_stk_push(
            institution=self.institution,
            invoice=invoice,
            phone_number="254712345678",
            amount=Decimal("600.00"),
            initiated_by_id=uuid.uuid4(),
        )
        self.assertEqual(stk_request.amount, Decimal("600.00"))


class HandleMpesaCallbackTests(FinanceServiceTestCase):
    def _invoice(self, amount_due="1000.00"):
        with bind_institution(self.institution):
            return Invoice.objects.create(
                institution_id=self.institution.id,
                student_id=uuid.uuid4(),
                term_id=uuid.uuid4(),
                amount_due=Decimal(amount_due),
            )

    def _pending_request(self, invoice, amount="1000.00"):
        with bind_institution(self.institution):
            return MpesaSTKPushRequest.objects.create(
                institution_id=self.institution.id,
                invoice=invoice,
                phone_number="254712345678",
                amount=Decimal(amount),
                verification_token="tok",
                checkout_request_id="ws_CO_1",
            )

    def _metadata(self, amount="1000.00", receipt="NLJ7RT61SV"):
        return {
            "amount": Decimal(amount),
            "mpesa_receipt_number": receipt,
            "transaction_date": timezone.now(),
            "phone_number": "254712345678",
        }

    def test_success_creates_payment_and_finalizes_the_invoice(self):
        invoice = self._invoice()
        stk_request = self._pending_request(invoice)

        result = handle_mpesa_callback(
            institution=self.institution,
            stk_request=stk_request,
            result_code=0,
            result_desc="The service request is processed successfully.",
            callback_metadata=self._metadata(),
        )

        self.assertEqual(result.status, MpesaSTKPushRequest.Status.SUCCESS)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, Invoice.Status.PAID)
        with bind_institution(self.institution):
            payment = Payment.objects.get(mpesa_transaction_id="NLJ7RT61SV")
            self.assertEqual(payment.method, Payment.Method.MPESA)
            self.assertTrue(payment.receipt.receipt_number.startswith("RCPT-"))

    def test_duplicate_callback_does_not_create_a_second_payment(self):
        invoice = self._invoice()
        stk_request = self._pending_request(invoice)
        handle_mpesa_callback(
            institution=self.institution,
            stk_request=stk_request,
            result_code=0,
            result_desc="ok",
            callback_metadata=self._metadata(),
        )
        stk_request.refresh_from_db()

        # Same request delivered again — Safaricom's own retry-on-timeout
        # behavior. Must be a no-op, not a second Payment.
        handle_mpesa_callback(
            institution=self.institution,
            stk_request=stk_request,
            result_code=0,
            result_desc="ok",
            callback_metadata=self._metadata(),
        )

        with bind_institution(self.institution):
            self.assertEqual(Payment.objects.filter(invoice=invoice).count(), 1)

    def test_cancelled_result_code_marks_the_request_cancelled(self):
        invoice = self._invoice()
        stk_request = self._pending_request(invoice)

        result = handle_mpesa_callback(
            institution=self.institution,
            stk_request=stk_request,
            result_code=1032,
            result_desc="Request cancelled by user",
            callback_metadata=None,
        )

        self.assertEqual(result.status, MpesaSTKPushRequest.Status.CANCELLED)
        with bind_institution(self.institution):
            self.assertEqual(Payment.objects.filter(invoice=invoice).count(), 0)

    def test_other_failure_result_code_marks_the_request_failed(self):
        invoice = self._invoice()
        stk_request = self._pending_request(invoice)

        result = handle_mpesa_callback(
            institution=self.institution,
            stk_request=stk_request,
            result_code=1037,
            result_desc="Timeout",
            callback_metadata=None,
        )

        self.assertEqual(result.status, MpesaSTKPushRequest.Status.FAILED)


class CreatePayrollRecordTests(FinanceServiceTestCase):
    def test_computes_net_as_gross_minus_deductions(self):
        record = create_payroll_record(
            institution=self.institution,
            staff_id=uuid.uuid4(),
            period="2026-01-01",
            gross=Decimal("50000.00"),
            deductions=[
                {"description": "PAYE", "amount": "8000.00"},
                {"description": "NHIF", "amount": "1700.00"},
            ],
            paid_at=timezone.now(),
        )

        self.assertEqual(record.net, Decimal("40300.00"))

    def test_net_may_go_negative_when_deductions_exceed_gross(self):
        record = create_payroll_record(
            institution=self.institution,
            staff_id=uuid.uuid4(),
            period="2026-01-01",
            gross=Decimal("10000.00"),
            deductions=[{"description": "Loan recovery", "amount": "12000.00"}],
            paid_at=timezone.now(),
        )

        self.assertEqual(record.net, Decimal("-2000.00"))

    def test_no_deductions_means_net_equals_gross(self):
        record = create_payroll_record(
            institution=self.institution,
            staff_id=uuid.uuid4(),
            period="2026-01-01",
            gross=Decimal("50000.00"),
            deductions=[],
            paid_at=timezone.now(),
        )

        self.assertEqual(record.net, Decimal("50000.00"))


class RecordExpenseTests(FinanceServiceTestCase):
    def test_creates_an_expense_record_with_the_given_approver(self):
        approver_id = uuid.uuid4()

        expense = record_expense(
            institution=self.institution,
            category="Utilities",
            amount=Decimal("2500.00"),
            incurred_at=timezone.now().date(),
            approved_by_id=approver_id,
        )

        self.assertEqual(expense.category, "Utilities")
        self.assertEqual(expense.approved_by_id, approver_id)
        with bind_institution(self.institution):
            self.assertEqual(ExpenseRecord.objects.count(), 1)

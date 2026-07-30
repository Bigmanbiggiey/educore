import uuid
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.core.context import bind_institution
from apps.finance.models import Invoice, Payment, Scholarship
from apps.finance.services import (
    create_fee_structure,
    generate_invoices_for_class,
    grant_scholarship,
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

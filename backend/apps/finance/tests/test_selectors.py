import uuid
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.core.context import bind_institution
from apps.finance.models import Invoice, Payment
from apps.finance.selectors import get_balance, get_institution_financial_summary
from apps.finance.services import record_payment
from apps.institutions.models import Institution


class FinanceSelectorTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")

    def _invoice(self, student_id, term_id, amount_due):
        with bind_institution(self.institution):
            return Invoice.objects.create(
                institution_id=self.institution.id,
                student_id=student_id,
                term_id=term_id,
                amount_due=Decimal(amount_due),
            )


class GetBalanceTests(FinanceSelectorTestCase):
    def test_balance_is_amount_due_minus_paid(self):
        student_id = uuid.uuid4()
        term_id = uuid.uuid4()
        invoice = self._invoice(student_id, term_id, "1000.00")
        record_payment(
            institution=self.institution,
            invoice=invoice,
            amount=Decimal("400.00"),
            method=Payment.Method.CASH,
            reference="",
            paid_at=timezone.now(),
            recorded_by_id=None,
        )

        balance = get_balance(self.institution, student_id, term_id)

        self.assertEqual(balance, Decimal("600.00"))

    def test_cancelled_invoices_are_excluded(self):
        student_id = uuid.uuid4()
        term_id = uuid.uuid4()
        invoice = self._invoice(student_id, term_id, "1000.00")
        with bind_institution(self.institution):
            invoice.status = Invoice.Status.CANCELLED
            invoice.save(update_fields=["status"])

        balance = get_balance(self.institution, student_id, term_id)

        self.assertEqual(balance, Decimal("0"))


class GetInstitutionFinancialSummaryTests(FinanceSelectorTestCase):
    def test_totals_invoiced_collected_and_outstanding(self):
        term_id = uuid.uuid4()
        invoice_one = self._invoice(uuid.uuid4(), term_id, "1000.00")
        self._invoice(uuid.uuid4(), term_id, "500.00")
        record_payment(
            institution=self.institution,
            invoice=invoice_one,
            amount=Decimal("300.00"),
            method=Payment.Method.MPESA,
            reference="ABC123",
            paid_at=timezone.now(),
            recorded_by_id=None,
        )

        summary = get_institution_financial_summary(self.institution, term_id)

        self.assertEqual(summary["total_invoiced"], Decimal("1500.00"))
        self.assertEqual(summary["total_collected"], Decimal("300.00"))
        self.assertEqual(summary["total_outstanding"], Decimal("1200.00"))
        self.assertEqual(summary["by_method"], {"mpesa": Decimal("300.00")})

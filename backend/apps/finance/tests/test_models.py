import uuid

from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.core.context import bind_institution
from apps.finance.models import FeeStructure, Payment, Receipt
from apps.institutions.models import Institution


class FinanceModelTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.ctx = bind_institution(self.institution)
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)


class FeeStructureConstraintTests(FinanceModelTestCase):
    def test_unique_per_class_term_name(self):
        class_grade_id = uuid.uuid4()
        term_id = uuid.uuid4()
        FeeStructure.objects.create(
            institution_id=self.institution.id,
            class_grade_id=class_grade_id,
            term_id=term_id,
            name="Tuition",
            line_items=[{"description": "Tuition", "amount": "1000.00"}],
            total_amount="1000.00",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                FeeStructure.objects.create(
                    institution_id=self.institution.id,
                    class_grade_id=class_grade_id,
                    term_id=term_id,
                    name="Tuition",
                    line_items=[],
                    total_amount="500.00",
                )

    def test_different_name_same_class_term_is_allowed(self):
        class_grade_id = uuid.uuid4()
        term_id = uuid.uuid4()
        FeeStructure.objects.create(
            institution_id=self.institution.id,
            class_grade_id=class_grade_id,
            term_id=term_id,
            name="Tuition",
            line_items=[],
            total_amount="1000.00",
        )
        FeeStructure.objects.create(
            institution_id=self.institution.id,
            class_grade_id=class_grade_id,
            term_id=term_id,
            name="Transport",
            line_items=[],
            total_amount="200.00",
        )  # must not raise


class PaymentConstraintTests(FinanceModelTestCase):
    def _invoice(self):
        from apps.finance.models import Invoice

        return Invoice.objects.create(
            institution_id=self.institution.id,
            student_id=uuid.uuid4(),
            term_id=uuid.uuid4(),
            amount_due="1000.00",
        )

    def test_amount_must_be_positive(self):
        invoice = self._invoice()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Payment.objects.create(
                    institution_id=self.institution.id,
                    invoice=invoice,
                    amount="0.00",
                    method=Payment.Method.CASH,
                    paid_at="2026-01-05T10:00:00Z",
                )


class ReceiptConstraintTests(FinanceModelTestCase):
    def test_unique_receipt_number_per_institution(self):
        from apps.finance.models import Invoice

        invoice = Invoice.objects.create(
            institution_id=self.institution.id,
            student_id=uuid.uuid4(),
            term_id=uuid.uuid4(),
            amount_due="1000.00",
        )
        payment_one = Payment.objects.create(
            institution_id=self.institution.id,
            invoice=invoice,
            amount="500.00",
            method=Payment.Method.CASH,
            paid_at="2026-01-05T10:00:00Z",
        )
        payment_two = Payment.objects.create(
            institution_id=self.institution.id,
            invoice=invoice,
            amount="500.00",
            method=Payment.Method.CASH,
            paid_at="2026-01-06T10:00:00Z",
        )
        Receipt.objects.create(
            institution_id=self.institution.id, payment=payment_one, receipt_number="RCPT-000001"
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Receipt.objects.create(
                    institution_id=self.institution.id,
                    payment=payment_two,
                    receipt_number="RCPT-000001",
                )

import decimal
import uuid

from django.test import TestCase

from apps.core.context import bind_institution
from apps.institutions.models import Institution
from apps.library.models import Book, BorrowerType, Copy, Fine, Loan
from apps.library.services import checkout, return_copy


class LibraryServiceTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        with bind_institution(self.institution):
            self.book = Book.objects.create(institution_id=self.institution.id, title="Emma")
            self.copy = Copy.objects.create(
                institution_id=self.institution.id, book=self.book, barcode="BC-1"
            )


class CheckoutTests(LibraryServiceTestCase):
    def test_creates_a_loan_and_marks_the_copy_on_loan(self):
        borrower_id = uuid.uuid4()
        loan = checkout(
            institution=self.institution,
            copy=self.copy,
            borrower_type=BorrowerType.STUDENT,
            borrower_id=borrower_id,
            due_date="2026-02-01",
        )

        self.assertEqual(loan.borrower_id, borrower_id)
        self.assertIsNone(loan.returned_at)
        self.copy.refresh_from_db()
        self.assertEqual(self.copy.status, Copy.Status.ON_LOAN)

    def test_rejects_checkout_of_a_copy_that_is_not_available(self):
        checkout(
            institution=self.institution,
            copy=self.copy,
            borrower_type=BorrowerType.STUDENT,
            borrower_id=uuid.uuid4(),
            due_date="2026-02-01",
        )

        with self.assertRaises(ValueError):
            checkout(
                institution=self.institution,
                copy=self.copy,
                borrower_type=BorrowerType.STAFF,
                borrower_id=uuid.uuid4(),
                due_date="2026-02-01",
            )

    def test_rejects_an_unknown_borrower_type(self):
        with self.assertRaises(ValueError):
            checkout(
                institution=self.institution,
                copy=self.copy,
                borrower_type="klingon",
                borrower_id=uuid.uuid4(),
                due_date="2026-02-01",
            )


class ReturnCopyTests(LibraryServiceTestCase):
    def _checkout(self):
        return checkout(
            institution=self.institution,
            copy=self.copy,
            borrower_type=BorrowerType.STUDENT,
            borrower_id=uuid.uuid4(),
            due_date="2026-02-01",
        )

    def test_marks_the_loan_returned_and_the_copy_available_again(self):
        loan = self._checkout()

        returned = return_copy(institution=self.institution, loan=loan)

        self.assertIsNotNone(returned.returned_at)
        self.copy.refresh_from_db()
        self.assertEqual(self.copy.status, Copy.Status.AVAILABLE)

    def test_lost_condition_marks_the_copy_lost_instead_of_available(self):
        loan = self._checkout()

        return_copy(institution=self.institution, loan=loan, condition="lost")

        self.copy.refresh_from_db()
        self.assertEqual(self.copy.status, Copy.Status.LOST)

    def test_optional_fine_is_recorded_against_the_loan(self):
        loan = self._checkout()

        return_copy(
            institution=self.institution,
            loan=loan,
            fine_amount=decimal.Decimal("50.00"),
            fine_reason="Returned late",
        )

        with bind_institution(self.institution):
            fine = Fine.objects.get(loan=loan)
        self.assertEqual(fine.amount, decimal.Decimal("50.00"))
        self.assertEqual(fine.reason, "Returned late")

    def test_rejects_returning_an_already_returned_loan(self):
        loan = self._checkout()
        return_copy(institution=self.institution, loan=loan)
        with bind_institution(self.institution):
            loan = Loan.objects.get(pk=loan.pk)

        with self.assertRaises(ValueError):
            return_copy(institution=self.institution, loan=loan)

    def test_rejects_an_unknown_condition(self):
        loan = self._checkout()
        with self.assertRaises(ValueError):
            return_copy(institution=self.institution, loan=loan, condition="klingon")

import uuid

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from apps.core.context import bind_institution
from apps.institutions.models import Institution
from apps.library.models import Book, BorrowerType, Copy, Loan, Reservation


class LibraryTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.ctx = bind_institution(self.institution)
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)
        self.book = Book.objects.create(
            institution_id=self.institution.id, title="Things Fall Apart"
        )

    def _copy(self, barcode="BC-1"):
        return Copy.objects.create(
            institution_id=self.institution.id, book=self.book, barcode=barcode
        )


class CopyConstraintTests(LibraryTestCase):
    def test_barcode_unique_per_institution(self):
        self._copy("BC-1")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._copy("BC-1")


class LoanConstraintTests(LibraryTestCase):
    def test_only_one_active_loan_per_copy(self):
        copy = self._copy()
        Loan.objects.create(
            institution_id=self.institution.id,
            copy=copy,
            borrower_type=BorrowerType.STUDENT,
            borrower_id=uuid.uuid4(),
            due_date="2026-02-01",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Loan.objects.create(
                    institution_id=self.institution.id,
                    copy=copy,
                    borrower_type=BorrowerType.STUDENT,
                    borrower_id=uuid.uuid4(),
                    due_date="2026-02-01",
                )

    def test_a_second_loan_is_allowed_once_the_first_is_returned(self):
        copy = self._copy()
        first = Loan.objects.create(
            institution_id=self.institution.id,
            copy=copy,
            borrower_type=BorrowerType.STUDENT,
            borrower_id=uuid.uuid4(),
            due_date="2026-02-01",
        )
        first.returned_at = timezone.now()
        first.save(update_fields=["returned_at"])

        Loan.objects.create(
            institution_id=self.institution.id,
            copy=copy,
            borrower_type=BorrowerType.STAFF,
            borrower_id=uuid.uuid4(),
            due_date="2026-03-01",
        )  # must not raise


class ReservationConstraintTests(LibraryTestCase):
    def test_only_one_pending_reservation_per_borrower_and_book(self):
        borrower_id = uuid.uuid4()
        Reservation.objects.create(
            institution_id=self.institution.id,
            book=self.book,
            borrower_type=BorrowerType.STUDENT,
            borrower_id=borrower_id,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Reservation.objects.create(
                    institution_id=self.institution.id,
                    book=self.book,
                    borrower_type=BorrowerType.STUDENT,
                    borrower_id=borrower_id,
                )

    def test_a_new_pending_reservation_is_allowed_once_the_first_is_no_longer_pending(self):
        borrower_id = uuid.uuid4()
        first = Reservation.objects.create(
            institution_id=self.institution.id,
            book=self.book,
            borrower_type=BorrowerType.STUDENT,
            borrower_id=borrower_id,
        )
        first.status = Reservation.Status.FULFILLED
        first.save(update_fields=["status"])

        Reservation.objects.create(
            institution_id=self.institution.id,
            book=self.book,
            borrower_type=BorrowerType.STUDENT,
            borrower_id=borrower_id,
        )  # must not raise

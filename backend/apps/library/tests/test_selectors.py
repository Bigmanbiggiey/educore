import datetime
import uuid

from django.test import TestCase

from apps.core.context import bind_institution
from apps.institutions.models import Institution
from apps.library.models import Book, BorrowerType, Copy, Loan
from apps.library.selectors import get_active_loans, get_available_copies, get_overdue_loans


class LibrarySelectorTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.ctx = bind_institution(self.institution)
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)
        self.book = Book.objects.create(institution_id=self.institution.id, title="Emma")

    def _copy(self, barcode, status=Copy.Status.AVAILABLE):
        return Copy.objects.create(
            institution_id=self.institution.id, book=self.book, barcode=barcode, status=status
        )


class GetAvailableCopiesTests(LibrarySelectorTestCase):
    def test_returns_only_available_copies_of_the_book(self):
        available = self._copy("BC-1")
        self._copy("BC-2", status=Copy.Status.ON_LOAN)

        results = get_available_copies(self.institution, self.book.id)

        self.assertEqual(results, [available])


class GetActiveLoansTests(LibrarySelectorTestCase):
    def test_returns_only_unreturned_loans_for_the_borrower(self):
        borrower_id = uuid.uuid4()
        copy = self._copy("BC-1")
        active = Loan.objects.create(
            institution_id=self.institution.id,
            copy=copy,
            borrower_type=BorrowerType.STUDENT,
            borrower_id=borrower_id,
            due_date="2026-02-01",
        )
        returned_copy = self._copy("BC-2")
        Loan.objects.create(
            institution_id=self.institution.id,
            copy=returned_copy,
            borrower_type=BorrowerType.STUDENT,
            borrower_id=borrower_id,
            due_date="2026-02-01",
            returned_at="2026-01-15T00:00:00+00:00",
        )

        results = get_active_loans(self.institution, BorrowerType.STUDENT, borrower_id)

        self.assertEqual(results, [active])


class GetOverdueLoansTests(LibrarySelectorTestCase):
    def test_returns_only_unreturned_loans_past_due_date(self):
        overdue_copy = self._copy("BC-1")
        overdue = Loan.objects.create(
            institution_id=self.institution.id,
            copy=overdue_copy,
            borrower_type=BorrowerType.STUDENT,
            borrower_id=uuid.uuid4(),
            due_date="2026-01-01",
        )
        not_due_copy = self._copy("BC-2")
        Loan.objects.create(
            institution_id=self.institution.id,
            copy=not_due_copy,
            borrower_type=BorrowerType.STUDENT,
            borrower_id=uuid.uuid4(),
            due_date="2026-12-01",
        )

        results = get_overdue_loans(self.institution, as_of=datetime.date(2026, 6, 1))

        self.assertEqual(results, [overdue])

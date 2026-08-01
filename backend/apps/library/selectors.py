"""Public read interface for `library` — docs/modules.md.

Every selector here takes `institution` explicitly and binds it via
`bind_institution`, same reasoning as every other Layer 1 app's
selectors.py module docstring.
"""

import datetime
import uuid

from apps.core.context import bind_institution
from apps.institutions.models import Institution
from apps.library.models import Copy, Loan


def get_available_copies(institution: Institution, book_id: uuid.UUID):
    with bind_institution(institution):
        return list(Copy.objects.filter(book_id=book_id, status=Copy.Status.AVAILABLE))


def get_active_loans(institution: Institution, borrower_type: str, borrower_id: uuid.UUID):
    with bind_institution(institution):
        return list(
            Loan.objects.filter(
                borrower_type=borrower_type, borrower_id=borrower_id, returned_at__isnull=True
            )
        )


def get_overdue_loans(institution: Institution, as_of: datetime.date | None = None):
    as_of = as_of or datetime.date.today()
    with bind_institution(institution):
        return list(Loan.objects.filter(returned_at__isnull=True, due_date__lt=as_of))

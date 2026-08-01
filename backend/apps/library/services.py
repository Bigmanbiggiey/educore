"""Public write interface for `library` — docs/modules.md:
`services.checkout(...)`, `services.return_copy(...)`.

Book/Copy/Reservation/Fine have no invariant beyond their own columns and
go through the ordinary DRF create/update path (`api.viewsets.TenantScopedModelViewSet`).
`checkout`/`return_copy` are pulled out into services because each one is a
two-model write with a real invariant that spans them: a checkout has to
confirm the copy is actually available before creating the `Loan` and flip
`Copy.status` alongside it; a return has to do the reverse and optionally
record a `Fine` in the same transaction. Same reasoning as
`timetable.assign_slot` and `admissions.services.make_offer`.
"""

import datetime
import decimal
import uuid

from django.db import transaction
from django.utils import timezone

from apps.core.context import bind_institution
from apps.institutions.models import Institution
from apps.library.models import BorrowerType, Copy, Fine, Loan

_RETURN_CONDITION_TO_COPY_STATUS = {
    "returned": Copy.Status.AVAILABLE,
    "lost": Copy.Status.LOST,
    "damaged": Copy.Status.DAMAGED,
}


@transaction.atomic
def checkout(
    *,
    institution: Institution,
    copy: Copy,
    borrower_type: str,
    borrower_id: uuid.UUID,
    due_date: datetime.date,
) -> Loan:
    if borrower_type not in BorrowerType.values:
        raise ValueError(f"Unknown borrower_type: {borrower_type!r}")
    with bind_institution(institution):
        if copy.status != Copy.Status.AVAILABLE:
            raise ValueError(
                f"Copy {copy.id} is not available for checkout (status: {copy.status!r})."
            )
        loan = Loan.objects.create(
            institution_id=institution.id,
            copy=copy,
            borrower_type=borrower_type,
            borrower_id=borrower_id,
            due_date=due_date,
        )
        copy.status = Copy.Status.ON_LOAN
        copy.save(update_fields=["status", "updated_at"])
    return loan


@transaction.atomic
def return_copy(
    *,
    institution: Institution,
    loan: Loan,
    condition: str = "returned",
    fine_amount: decimal.Decimal | None = None,
    fine_reason: str = "",
) -> Loan:
    if loan.returned_at is not None:
        raise ValueError(f"Loan {loan.id} has already been returned.")
    if condition not in _RETURN_CONDITION_TO_COPY_STATUS:
        raise ValueError(f"Unknown condition: {condition!r}")
    with bind_institution(institution):
        loan.returned_at = timezone.now()
        loan.save(update_fields=["returned_at", "updated_at"])
        copy = loan.copy
        copy.status = _RETURN_CONDITION_TO_COPY_STATUS[condition]
        copy.save(update_fields=["status", "updated_at"])
        if fine_amount is not None:
            Fine.objects.create(
                institution_id=institution.id,
                loan=loan,
                amount=fine_amount,
                reason=fine_reason,
            )
    return loan

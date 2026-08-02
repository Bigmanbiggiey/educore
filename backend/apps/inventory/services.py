"""Public write interface for `inventory` — docs/modules.md:
`services.record_movement(...)`.

`Supplier`/`Asset`/`StockItem` have no invariant beyond their own columns —
`create_supplier`/`create_asset`/`create_stock_item` are plain wrappers, the
same "public write API for this app's tables" shape `classes_streams` and
`timetable` establish for their own plain-create models. `record_movement`
is the one function worth pulling out for real: it is a two-model write
with a real invariant spanning them — a stock-out can't be recorded past
what's actually on hand, and `StockItem.quantity_on_hand` has to move in
the same transaction as the `StockMovement` row that justifies it — same
reasoning as `library.services.checkout`/`return_copy`.
"""

from django.db import transaction

from apps.core.context import bind_institution
from apps.institutions.models import Institution
from apps.inventory.models import Asset, StockItem, StockMovement, Supplier


def create_supplier(
    *,
    institution: Institution,
    name: str,
    contact_person: str = "",
    phone: str = "",
    email: str = "",
) -> Supplier:
    with bind_institution(institution):
        return Supplier.objects.create(
            institution_id=institution.id,
            name=name,
            contact_person=contact_person,
            phone=phone,
            email=email,
        )


def create_asset(
    *,
    institution: Institution,
    name: str,
    category: str = "",
    serial_number: str = "",
    supplier: Supplier | None = None,
) -> Asset:
    with bind_institution(institution):
        return Asset.objects.create(
            institution_id=institution.id,
            name=name,
            category=category,
            serial_number=serial_number,
            supplier=supplier,
        )


def create_stock_item(
    *, institution: Institution, name: str, unit: str = "", supplier: Supplier | None = None
) -> StockItem:
    with bind_institution(institution):
        return StockItem.objects.create(
            institution_id=institution.id, name=name, unit=unit, supplier=supplier
        )


@transaction.atomic
def record_movement(
    *,
    institution: Institution,
    stock_item: StockItem,
    direction: str,
    quantity: int,
    reason: str = "",
) -> StockMovement:
    if direction not in StockMovement.Direction.values:
        raise ValueError(f"Unknown direction: {direction!r}")
    if quantity <= 0:
        raise ValueError("quantity must be a positive integer")
    with bind_institution(institution):
        if direction == StockMovement.Direction.OUT and quantity > stock_item.quantity_on_hand:
            raise ValueError(
                f"Insufficient stock for {stock_item}: have {stock_item.quantity_on_hand}, "
                f"need {quantity}."
            )
        movement = StockMovement.objects.create(
            institution_id=institution.id,
            stock_item=stock_item,
            direction=direction,
            quantity=quantity,
            reason=reason,
        )
        delta = quantity if direction == StockMovement.Direction.IN else -quantity
        stock_item.quantity_on_hand += delta
        stock_item.save(update_fields=["quantity_on_hand", "updated_at"])
    return movement

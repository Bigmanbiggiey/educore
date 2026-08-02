"""Public read interface for `inventory` — docs/modules.md."""

import uuid

from apps.core.context import bind_institution
from apps.institutions.models import Institution
from apps.inventory.models import Asset, StockItem, StockMovement


def get_stock_level(institution: Institution, stock_item_id: uuid.UUID) -> int:
    with bind_institution(institution):
        return StockItem.objects.get(pk=stock_item_id).quantity_on_hand


def get_movements(institution: Institution, stock_item_id: uuid.UUID):
    with bind_institution(institution):
        return list(StockMovement.objects.filter(stock_item_id=stock_item_id))


def get_assets_by_status(institution: Institution, status: str):
    with bind_institution(institution):
        return list(Asset.objects.filter(status=status))

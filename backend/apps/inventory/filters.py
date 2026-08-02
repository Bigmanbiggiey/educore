"""Explicit filter whitelist for `inventory.StockMovement` — docs/api-design.md
§6: hand-declared, not auto-derived from `Meta.fields` (see
`attendance.filters`'s module docstring for the full explanation this
project reuses everywhere).
"""

import django_filters

from apps.inventory.models import StockMovement


class StockMovementFilterSet(django_filters.FilterSet):
    stock_item = django_filters.UUIDFilter(field_name="stock_item_id")
    direction = django_filters.ChoiceFilter(
        field_name="direction", choices=StockMovement.Direction.choices
    )

    class Meta:
        model = StockMovement
        fields = ["stock_item", "direction"]

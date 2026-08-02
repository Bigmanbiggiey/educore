from django.test import TestCase

from apps.core.context import bind_institution
from apps.institutions.models import Institution
from apps.inventory.models import Asset, StockItem
from apps.inventory.selectors import get_assets_by_status, get_movements, get_stock_level
from apps.inventory.services import record_movement


class InventorySelectorTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.ctx = bind_institution(self.institution)
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)


class GetStockLevelTests(InventorySelectorTestCase):
    def test_returns_the_current_quantity_on_hand(self):
        item = StockItem.objects.create(institution_id=self.institution.id, name="Chalk")
        record_movement(institution=self.institution, stock_item=item, direction="in", quantity=7)

        self.assertEqual(get_stock_level(self.institution, item.id), 7)


class GetMovementsTests(InventorySelectorTestCase):
    def test_returns_only_movements_for_the_item(self):
        item = StockItem.objects.create(institution_id=self.institution.id, name="Chalk")
        other = StockItem.objects.create(institution_id=self.institution.id, name="Paper")
        movement = record_movement(
            institution=self.institution, stock_item=item, direction="in", quantity=3
        )
        record_movement(institution=self.institution, stock_item=other, direction="in", quantity=3)

        self.assertEqual(get_movements(self.institution, item.id), [movement])


class GetAssetsByStatusTests(InventorySelectorTestCase):
    def test_returns_only_assets_with_the_given_status(self):
        in_use = Asset.objects.create(
            institution_id=self.institution.id, name="Laptop", status=Asset.Status.IN_USE
        )
        Asset.objects.create(
            institution_id=self.institution.id, name="Projector", status=Asset.Status.IN_STORE
        )

        self.assertEqual(get_assets_by_status(self.institution, Asset.Status.IN_USE), [in_use])

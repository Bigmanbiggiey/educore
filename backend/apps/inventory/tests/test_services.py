from django.test import TestCase

from apps.core.context import bind_institution
from apps.institutions.models import Institution
from apps.inventory.models import StockItem, StockMovement
from apps.inventory.services import record_movement


class InventoryServiceTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        with bind_institution(self.institution):
            self.item = StockItem.objects.create(institution_id=self.institution.id, name="Chalk")


class RecordMovementTests(InventoryServiceTestCase):
    def test_an_in_movement_increases_quantity_on_hand(self):
        record_movement(
            institution=self.institution,
            stock_item=self.item,
            direction=StockMovement.Direction.IN,
            quantity=10,
        )
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity_on_hand, 10)

    def test_an_out_movement_decreases_quantity_on_hand(self):
        record_movement(
            institution=self.institution,
            stock_item=self.item,
            direction=StockMovement.Direction.IN,
            quantity=10,
        )
        record_movement(
            institution=self.institution,
            stock_item=self.item,
            direction=StockMovement.Direction.OUT,
            quantity=4,
        )
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity_on_hand, 6)

    def test_rejects_an_out_movement_exceeding_stock_on_hand(self):
        with self.assertRaises(ValueError):
            record_movement(
                institution=self.institution,
                stock_item=self.item,
                direction=StockMovement.Direction.OUT,
                quantity=1,
            )
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity_on_hand, 0)

    def test_rejects_an_unknown_direction(self):
        with self.assertRaises(ValueError):
            record_movement(
                institution=self.institution, stock_item=self.item, direction="sideways", quantity=1
            )

    def test_rejects_a_non_positive_quantity(self):
        with self.assertRaises(ValueError):
            record_movement(
                institution=self.institution,
                stock_item=self.item,
                direction=StockMovement.Direction.IN,
                quantity=0,
            )

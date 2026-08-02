from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.core.context import bind_institution
from apps.institutions.models import Institution
from apps.inventory.models import StockItem, StockMovement


class InventoryTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.ctx = bind_institution(self.institution)
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)
        self.item = StockItem.objects.create(institution_id=self.institution.id, name="Chalk")


class StockMovementConstraintTests(InventoryTestCase):
    def test_quantity_must_be_positive(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                StockMovement.objects.create(
                    institution_id=self.institution.id,
                    stock_item=self.item,
                    direction=StockMovement.Direction.IN,
                    quantity=0,
                )

    def test_a_positive_quantity_is_allowed(self):
        StockMovement.objects.create(
            institution_id=self.institution.id,
            stock_item=self.item,
            direction=StockMovement.Direction.IN,
            quantity=5,
        )  # must not raise

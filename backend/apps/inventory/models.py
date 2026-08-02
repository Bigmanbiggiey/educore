"""Layer 1 models — docs/database.md §3 ("Library, Inventory, Transport,
Hostel, Clinic"):

    Asset, StockItem → StockMovement (in/out, quantity, reason)

`Supplier` is named in docs/modules.md's own entity list for this app
(`Asset`, `StockItem`, `StockMovement`, `Supplier`) even though the
database.md entity sketch doesn't spell out its fields — it's a plain
contact-details record `Asset`/`StockItem` optionally reference, same
"not fully specced at design time, fixed at implementation time" note
docs/database.md §5 makes for this whole entity group. None of the four
are on docs/database.md §1's soft-delete list, so all four are plain
`TenantScopedModel`.
"""

from django.db import models

from apps.core.models import TenantScopedModel


class Supplier(TenantScopedModel):
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Asset(TenantScopedModel):
    class Status(models.TextChoices):
        IN_USE = "in_use", "In Use"
        IN_STORE = "in_store", "In Store"
        UNDER_REPAIR = "under_repair", "Under Repair"
        DISPOSED = "disposed", "Disposed"

    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.IN_STORE)
    # SET_NULL, not CASCADE: a supplier going out of business shouldn't
    # silently delete every asset it ever supplied — same reasoning as
    # `library.Copy`'s FK-to-parent choices elsewhere in this codebase, just
    # applied to an optional reference instead of a required one.
    supplier = models.ForeignKey(
        Supplier, null=True, blank=True, on_delete=models.SET_NULL, related_name="assets"
    )
    acquired_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class StockItem(TenantScopedModel):
    name = models.CharField(max_length=255)
    unit = models.CharField(max_length=50, blank=True)
    # Denormalized running total, not directly writable via the API
    # (read-only in `StockItemSerializer`) — the only sanctioned way to
    # change it is `services.record_movement`, same "managed field" shape
    # `library.Copy.status` established for a value only a service mutates.
    quantity_on_hand = models.PositiveIntegerField(default=0)
    supplier = models.ForeignKey(
        Supplier, null=True, blank=True, on_delete=models.SET_NULL, related_name="stock_items"
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class StockMovement(TenantScopedModel):
    class Direction(models.TextChoices):
        IN = "in", "In"
        OUT = "out", "Out"

    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name="movements")
    direction = models.CharField(max_length=3, choices=Direction.choices)
    quantity = models.PositiveIntegerField()
    reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]

    Meta.constraints = [
        models.CheckConstraint(
            condition=models.Q(quantity__gt=0), name="stockmovement_quantity_positive"
        ),
    ]

    def __str__(self) -> str:
        return f"{self.stock_item} — {self.get_direction_display()} {self.quantity}"

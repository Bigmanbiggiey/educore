"""Layer 1 models — docs/database.md §3 ("Library, Inventory, Transport,
Hostel, Clinic"):

    Book → Copy (1:many) → Loan (copy, borrower[Student|Staff via generic FK],
                                  due_date) → Fine

`borrower` is modeled as a `borrower_type` discriminator + plain
`borrower_id` UUID, not Django's `contenttypes` generic FK — same
convention `attendance.AttendanceRecord` already established for a
Student|Staff reference (`subject_type`/`target_id`), kept here for
consistency and to avoid introducing `django.contrib.contenttypes` as a new
dependency for a single field. None of these four are on
docs/database.md §1's soft-delete list, so all four are plain
`TenantScopedModel`.
"""

from django.db import models

from apps.core.models import TenantScopedModel


class BorrowerType(models.TextChoices):
    STUDENT = "student", "Student"
    STAFF = "staff", "Staff"


class Book(TenantScopedModel):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, blank=True)
    isbn = models.CharField(max_length=20, blank=True)
    category = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title


class Copy(TenantScopedModel):
    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        ON_LOAN = "on_loan", "On Loan"
        LOST = "lost", "Lost"
        DAMAGED = "damaged", "Damaged"

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="copies")
    barcode = models.CharField(max_length=50)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.AVAILABLE)

    class Meta:
        ordering = ["barcode"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "barcode"], name="copy_unique_barcode_per_institution"
        ),
    ]

    def __str__(self) -> str:
        return f"{self.book.title} — {self.barcode}"


class Loan(TenantScopedModel):
    copy = models.ForeignKey(Copy, on_delete=models.CASCADE, related_name="loans")
    borrower_type = models.CharField(max_length=10, choices=BorrowerType.choices)
    borrower_id = models.UUIDField()
    due_date = models.DateField()
    returned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    Meta.constraints = [
        # A copy can only be on one active (unreturned) loan at a time —
        # `services.checkout` also checks `Copy.status` before writing, but
        # this holds even against direct ORM access that bypasses it.
        models.UniqueConstraint(
            fields=["copy"],
            condition=models.Q(returned_at__isnull=True),
            name="loan_one_active_per_copy",
        ),
    ]

    def __str__(self) -> str:
        return f"{self.copy} — {self.get_borrower_type_display()} {self.borrower_id}"


class Reservation(TenantScopedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        FULFILLED = "fulfilled", "Fulfilled"
        CANCELLED = "cancelled", "Cancelled"

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="reservations")
    borrower_type = models.CharField(max_length=10, choices=BorrowerType.choices)
    borrower_id = models.UUIDField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)

    class Meta:
        ordering = ["-created_at"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["book", "borrower_type", "borrower_id"],
            condition=models.Q(status=Status.PENDING),
            name="reservation_one_pending_per_borrower_book",
        ),
    ]

    def __str__(self) -> str:
        return (
            f"{self.book} — {self.get_borrower_type_display()} {self.borrower_id} — "
            f"{self.get_status_display()}"
        )


class Fine(TenantScopedModel):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="fines")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.CharField(max_length=255, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Fine {self.amount} — {self.loan}"

from django.contrib import admin

from apps.library.models import Book, Copy, Fine, Loan, Reservation


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "isbn")
    search_fields = ("title", "author", "isbn")


@admin.register(Copy)
class CopyAdmin(admin.ModelAdmin):
    list_display = ("book", "barcode", "status")
    list_filter = ("status",)


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ("copy", "borrower_type", "borrower_id", "due_date", "returned_at")
    list_filter = ("borrower_type",)


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("book", "borrower_type", "borrower_id", "status")
    list_filter = ("status",)


@admin.register(Fine)
class FineAdmin(admin.ModelAdmin):
    list_display = ("loan", "amount", "paid_at")

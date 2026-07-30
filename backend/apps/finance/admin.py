from django.contrib import admin

from apps.finance.models import (
    FeeStructure,
    InstallmentPlan,
    Invoice,
    Payment,
    Receipt,
    Scholarship,
)


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ("name", "institution_id", "class_grade_id", "term_id", "total_amount")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("id", "institution_id", "student_id", "term_id", "amount_due", "status")
    list_filter = ("status",)


@admin.register(InstallmentPlan)
class InstallmentPlanAdmin(admin.ModelAdmin):
    list_display = ("invoice", "num_installments")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("invoice", "amount", "method", "paid_at", "recorded_by_id")
    list_filter = ("method",)


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ("receipt_number", "payment")


@admin.register(Scholarship)
class ScholarshipAdmin(admin.ModelAdmin):
    list_display = ("student_id", "term_id", "amount_or_percent", "is_percent", "funded_by")

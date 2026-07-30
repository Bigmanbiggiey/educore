"""Request/response shapes for `finance`'s API surface — docs/api-design.md."""

from rest_framework import serializers

from api.serializers import TenantScopedModelSerializer
from apps.finance.models import (
    ExpenseRecord,
    FeeStructure,
    InstallmentPlan,
    Invoice,
    MpesaSTKPushRequest,
    Payment,
    Payroll,
    Receipt,
    Scholarship,
)


class FeeStructureLineItemSerializer(serializers.Serializer):
    description = serializers.CharField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)


class FeeStructureSerializer(TenantScopedModelSerializer):
    line_items = FeeStructureLineItemSerializer(many=True)

    class Meta:
        model = FeeStructure
        fields = [
            "id",
            "class_grade_id",
            "term_id",
            "name",
            "line_items",
            "total_amount",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "total_amount", "created_at", "updated_at"]
        extra_kwargs = {
            "class_grade_id": {
                "help_text": "classes_streams.ClassGrade this fee structure applies to."
            },
            "term_id": {"help_text": "classes_streams.Term this fee structure applies to."},
            "line_items": {"help_text": "List of {description, amount}; total_amount is derived."},
        }


class InvoiceSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Invoice
        fields = [
            "id",
            "student_id",
            "term_id",
            "fee_structure_id",
            "amount_due",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at"]
        extra_kwargs = {
            "student_id": {"help_text": "students.Student this invoice belongs to."},
            "term_id": {"help_text": "classes_streams.Term this invoice belongs to."},
            "fee_structure_id": {
                "help_text": "Optional — null for an ad hoc invoice with no FeeStructure behind it."
            },
        }


class InstallmentScheduleItemSerializer(serializers.Serializer):
    due_date = serializers.DateField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)


class InstallmentPlanSerializer(TenantScopedModelSerializer):
    schedule = InstallmentScheduleItemSerializer(many=True)

    class Meta:
        model = InstallmentPlan
        fields = ["id", "invoice", "num_installments", "schedule", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class PaymentSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "invoice",
            "amount",
            "method",
            "reference",
            "paid_at",
            "recorded_by_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "recorded_by_id", "created_at", "updated_at"]
        extra_kwargs = {
            "method": {"help_text": "mpesa (manually-reconciled reference), cash, or bank."},
        }


class ReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipt
        fields = ["id", "payment", "receipt_number", "pdf_document", "created_at"]
        read_only_fields = fields


class ScholarshipSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Scholarship
        fields = [
            "id",
            "student_id",
            "term_id",
            "amount_or_percent",
            "is_percent",
            "funded_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "is_percent": {
                "help_text": "True if amount_or_percent is a percentage, not a flat amount."
            },
        }


class GenerateInvoicesResponseSerializer(serializers.Serializer):
    created = serializers.IntegerField()


class InitiateMpesaPaymentSerializer(serializers.Serializer):
    """`phone_number` is only honored for a Finance-Officer-initiated push
    (`finance.payment.record`) — a self-service Parent's phone number is
    always their own on-file `accounts.User.phone`, never client-supplied
    (`views.py`'s dual-path handling, not this serializer). `amount`
    defaults to the invoice's full remaining balance when omitted."""

    phone_number = serializers.CharField(required=False, allow_blank=True)
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )


class MpesaSTKPushRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = MpesaSTKPushRequest
        fields = [
            "id",
            "invoice",
            "phone_number",
            "amount",
            "status",
            "checkout_request_id",
            "result_desc",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class FinancialSummarySerializer(serializers.Serializer):
    term_id = serializers.CharField()
    total_invoiced = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_collected = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_outstanding = serializers.DecimalField(max_digits=14, decimal_places=2)
    by_method = serializers.DictField()


class PayrollDeductionItemSerializer(serializers.Serializer):
    description = serializers.CharField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)


class PayrollSerializer(TenantScopedModelSerializer):
    deductions = PayrollDeductionItemSerializer(many=True)

    class Meta:
        model = Payroll
        fields = [
            "id",
            "staff_id",
            "period",
            "gross",
            "deductions",
            "net",
            "paid_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "net", "created_at", "updated_at"]
        extra_kwargs = {
            "staff_id": {"help_text": "staff.StaffProfile this payroll record belongs to."},
            "period": {"help_text": "First day of the pay-period month, e.g. 2026-01-01."},
            "deductions": {"help_text": "List of {description, amount}; net is derived."},
        }


class ExpenseRecordSerializer(TenantScopedModelSerializer):
    class Meta:
        model = ExpenseRecord
        fields = [
            "id",
            "category",
            "amount",
            "incurred_at",
            "approved_by_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "approved_by_id", "created_at", "updated_at"]

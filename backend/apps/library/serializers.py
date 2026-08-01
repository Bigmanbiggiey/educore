"""Request/response shapes for `library`'s API surface — docs/api-design.md.
`Loan.returned_at` is read-only — it only ever changes via the dedicated
`return` RPC action, never an overloaded `PATCH` (§1), same convention
`admissions.Application.stage` established.
"""

from rest_framework import serializers

from api.serializers import TenantScopedModelSerializer
from apps.library.models import Book, Copy, Fine, Loan, Reservation


class BookSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Book
        fields = ["id", "title", "author", "isbn", "category", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class CopySerializer(TenantScopedModelSerializer):
    class Meta:
        model = Copy
        fields = ["id", "book", "barcode", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class LoanSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Loan
        fields = [
            "id",
            "copy",
            "borrower_type",
            "borrower_id",
            "due_date",
            "returned_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "returned_at", "created_at", "updated_at"]
        extra_kwargs = {
            "borrower_id": {
                "help_text": "students.Student.id or staff.StaffProfile.id, per borrower_type."
            },
        }


class ReturnLoanSerializer(serializers.Serializer):
    condition = serializers.ChoiceField(
        choices=["returned", "lost", "damaged"], default="returned"
    )
    fine_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True, default=None
    )
    fine_reason = serializers.CharField(
        max_length=255, required=False, allow_blank=True, default=""
    )


class ReservationSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Reservation
        fields = [
            "id",
            "book",
            "borrower_type",
            "borrower_id",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class FineSerializer(TenantScopedModelSerializer):
    class Meta:
        model = Fine
        fields = ["id", "loan", "amount", "reason", "paid_at", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

"""API views for `library` — docs/api-design.md. `Loan` creation routes
through `services.checkout` (has to check copy availability and flip
`Copy.status` alongside the write — the generic create path can't do that,
same reasoning as `timetable.SubjectSlotAssignmentViewSet`) and returning a
loan is a dedicated RPC-style action, not an overloaded `PATCH` (§1), same
convention `admissions`'s `accept-offer` established for a real lifecycle
transition.
"""

from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from api.viewsets import TenantScopedModelViewSet
from apps.library import services
from apps.library.filters import LoanFilterSet
from apps.library.models import Book, Copy, Fine, Loan, Reservation
from apps.library.serializers import (
    BookSerializer,
    CopySerializer,
    FineSerializer,
    LoanSerializer,
    ReservationSerializer,
    ReturnLoanSerializer,
)
from apps.permissions.permissions import HasPermission, IsInstitutionMember

_WRITE_ACTIONS = ("create", "update", "partial_update", "destroy")


def _write_gated_by(permission_code):
    def get_permissions(self):
        if self.action in _WRITE_ACTIONS or self.action == "return_loan":
            return [IsInstitutionMember(), HasPermission(permission_code)()]
        return [IsInstitutionMember()]

    return get_permissions


class BookViewSet(TenantScopedModelViewSet):
    queryset_model = Book
    serializer_class = BookSerializer
    get_permissions = _write_gated_by("library.book.manage")


class CopyViewSet(TenantScopedModelViewSet):
    queryset_model = Copy
    serializer_class = CopySerializer
    get_permissions = _write_gated_by("library.copy.manage")


class LoanViewSet(TenantScopedModelViewSet):
    queryset_model = Loan
    serializer_class = LoanSerializer
    filterset_class = LoanFilterSet
    get_permissions = _write_gated_by("library.loan.manage")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            loan = services.checkout(institution=request.institution, **serializer.validated_data)
        except ValueError as exc:
            raise ValidationError({"detail": [str(exc)]}) from exc
        return Response(self.get_serializer(loan).data, status=201)

    @action(detail=True, methods=["post"], url_path="return", url_name="return")
    def return_loan(self, request, pk=None):
        loan = self.get_object()
        serializer = ReturnLoanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            loan = services.return_copy(
                institution=request.institution, loan=loan, **serializer.validated_data
            )
        except ValueError as exc:
            raise ValidationError({"detail": [str(exc)]}) from exc
        return Response(self.get_serializer(loan).data)


class ReservationViewSet(TenantScopedModelViewSet):
    queryset_model = Reservation
    serializer_class = ReservationSerializer
    get_permissions = _write_gated_by("library.reservation.manage")


class FineViewSet(TenantScopedModelViewSet):
    queryset_model = Fine
    serializer_class = FineSerializer
    get_permissions = _write_gated_by("library.fine.manage")

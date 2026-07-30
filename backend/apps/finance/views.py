"""API views for `finance` — docs/api-design.md.

`InvoiceViewSet` reads are object-scoped for Parent/Student, same
fail-closed pattern as `students.StudentViewSet`/`academics.ReportCardView`
— a Parent sees only their own children's invoices, a Student only their
own, regardless of any broader permission either might also hold. This is
the one place `finance` genuinely imports `apps.students` (read-only
selectors), which is why `finance` gets its own `.importlinter`
dependency contract (`finance-dependencies`) rather than joining the flat
Layer-1-siblings-independent set — same shape `academics` already
established for the identical reason.

`InstallmentPlanViewSet`/`PaymentViewSet` writes route through
`services.py` rather than the generic save path (real invariants beyond a
`UniqueConstraint`: `record_payment` recomputes `Invoice.status` and
creates a `Receipt`), same pattern as
`timetable.SubjectSlotAssignmentViewSet`/`attendance.AttendanceRecordViewSet`.
"""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from api.idempotency import replay_or_execute
from api.viewsets import TenantScopedModelViewSet
from apps.finance import services
from apps.finance.filters import InvoiceFilterSet, PaymentFilterSet
from apps.finance.models import (
    FeeStructure,
    InstallmentPlan,
    Invoice,
    Payment,
    Receipt,
    Scholarship,
)
from apps.finance.selectors import get_institution_financial_summary
from apps.finance.serializers import (
    FeeStructureSerializer,
    FinancialSummarySerializer,
    GenerateInvoicesResponseSerializer,
    InstallmentPlanSerializer,
    InvoiceSerializer,
    PaymentSerializer,
    ReceiptSerializer,
    ScholarshipSerializer,
)
from apps.permissions.permissions import HasPermission, IsInstitutionMember
from apps.permissions.selectors import get_membership_access
from apps.students.selectors import get_active_roster, get_guardian_children, get_student_by_user_id

_WRITE_ACTIONS = ("create", "update", "partial_update", "destroy")


def _view_and_manage(view_permission_code, manage_permission_code, extra_action_codes=None):
    """Reads gated by `view_permission_code`, writes additionally require
    `manage_permission_code` — finance data isn't open to every active
    member the way, say, the academic calendar is (docs/permissions.md
    §5: Principal/Deputy Principal are finance view-only).
    `extra_action_codes` maps a custom `@action` name to its own permission
    code (e.g. the `generate-invoices` RPC action)."""
    extra_action_codes = extra_action_codes or {}

    def get_permissions(self):
        if self.action in extra_action_codes:
            return [IsInstitutionMember(), HasPermission(extra_action_codes[self.action])()]
        if self.action in _WRITE_ACTIONS:
            return [IsInstitutionMember(), HasPermission(manage_permission_code)()]
        return [IsInstitutionMember(), HasPermission(view_permission_code)()]

    return get_permissions


class FeeStructureViewSet(TenantScopedModelViewSet):
    queryset_model = FeeStructure
    serializer_class = FeeStructureSerializer
    get_permissions = _view_and_manage(
        "finance.invoice.view",
        "finance.fee_structure.manage",
        extra_action_codes={"generate_invoices": "finance.invoice.generate"},
    )

    def perform_create(self, serializer):
        serializer.instance = services.create_fee_structure(
            institution=self.request.institution, **serializer.validated_data
        )

    @action(detail=True, methods=["post"], url_path="generate-invoices")
    def generate_invoices(self, request, pk=None):
        fee_structure = self.get_object()
        roster = get_active_roster(fee_structure.class_grade_id)
        student_ids = list(roster.values_list("id", flat=True))
        invoices = services.generate_invoices_for_class(
            institution=request.institution, fee_structure=fee_structure, student_ids=student_ids
        )
        return Response(
            GenerateInvoicesResponseSerializer({"created": len(invoices)}).data, status=201
        )


class InvoiceViewSet(TenantScopedModelViewSet):
    queryset_model = Invoice
    serializer_class = InvoiceSerializer
    filterset_class = InvoiceFilterSet
    get_permissions = _view_and_manage("finance.invoice.view", "finance.invoice.manage")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.get_base_queryset()

        access = get_membership_access(self.request.user, self.request.institution)
        # Fail-closed, regardless of any broader grant — same precedent as
        # students.StudentViewSet/academics.ReportCardView.
        if "Parent" in access.role_names:
            child_ids = get_guardian_children(self.request.user.id).values_list("id", flat=True)
            return self.get_base_queryset().filter(student_id__in=child_ids)
        if "Student" in access.role_names:
            student = get_student_by_user_id(self.request.user.id)
            if student is None:
                return self.get_base_queryset().none()
            return self.get_base_queryset().filter(student_id=student.id)
        return self.get_base_queryset()


class InstallmentPlanViewSet(TenantScopedModelViewSet):
    queryset_model = InstallmentPlan
    serializer_class = InstallmentPlanSerializer
    get_permissions = _view_and_manage("finance.invoice.view", "finance.installment_plan.manage")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plan = services.set_installment_plan(
            institution=request.institution, **serializer.validated_data
        )
        return Response(self.get_serializer(plan).data, status=201)


class PaymentViewSet(TenantScopedModelViewSet):
    queryset_model = Payment
    serializer_class = PaymentSerializer
    filterset_class = PaymentFilterSet
    get_permissions = _view_and_manage("finance.invoice.view", "finance.payment.record")

    def create(self, request, *args, **kwargs):
        def _record():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            actor = request.user if request.user.is_authenticated else None
            try:
                payment = services.record_payment(
                    institution=request.institution,
                    recorded_by_id=actor.id if actor else None,
                    **serializer.validated_data,
                )
            except ValueError as exc:
                raise ValidationError({"amount": [str(exc)]}) from exc
            return Response(self.get_serializer(payment).data, status=201)

        return replay_or_execute(
            request,
            scope="finance.payment.record",
            institution_id=request.institution.id,
            fn=_record,
        )


class ReceiptViewSet(ReadOnlyModelViewSet):
    """Read-only — a `Receipt` is only ever auto-created by
    `services.record_payment`, never directly by a client."""

    serializer_class = ReceiptSerializer

    def get_permissions(self):
        return [IsInstitutionMember(), HasPermission("finance.invoice.view")()]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Receipt.all_tenants_unsafe.none()
        return Receipt.objects.all()


class ScholarshipViewSet(TenantScopedModelViewSet):
    queryset_model = Scholarship
    serializer_class = ScholarshipSerializer
    get_permissions = _view_and_manage("finance.invoice.view", "finance.scholarship.manage")

    def perform_create(self, serializer):
        serializer.instance = services.grant_scholarship(
            institution=self.request.institution, **serializer.validated_data
        )


class FinancialSummaryView(APIView):
    """`GET /api/v1/finance/reports/summary/?term_id=<uuid>` — the basic
    "Financial Reports" deliverable (docs/roadmap.md Phase 4). Deeper
    analytics/exports are `analytics`/`reports` territory later (Phase 8)."""

    permission_classes = [IsInstitutionMember, HasPermission("finance.report.view")]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "term_id", OpenApiTypes.UUID, required=True, description="classes_streams.Term"
            )
        ],
        responses={200: FinancialSummarySerializer},
    )
    def get(self, request):
        term_id = request.query_params.get("term_id")
        if not term_id:
            raise ValidationError({"term_id": ["This query parameter is required."]})
        summary = get_institution_financial_summary(request.institution, term_id)
        return Response(FinancialSummarySerializer(summary).data)

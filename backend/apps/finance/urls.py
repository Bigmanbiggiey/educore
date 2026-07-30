from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.finance.views import (
    FeeStructureViewSet,
    FinancialSummaryView,
    InstallmentPlanViewSet,
    InvoiceViewSet,
    PaymentViewSet,
    ReceiptViewSet,
    ScholarshipViewSet,
)

app_name = "finance"

router = DefaultRouter()
router.register("fee-structures", FeeStructureViewSet, basename="fee-structure")
router.register("invoices", InvoiceViewSet, basename="invoice")
router.register("installment-plans", InstallmentPlanViewSet, basename="installment-plan")
router.register("payments", PaymentViewSet, basename="payment")
router.register("receipts", ReceiptViewSet, basename="receipt")
router.register("scholarships", ScholarshipViewSet, basename="scholarship")

urlpatterns = [
    *router.urls,
    path("finance/reports/summary/", FinancialSummaryView.as_view(), name="financial-summary"),
]

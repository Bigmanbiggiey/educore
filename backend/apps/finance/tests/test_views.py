import uuid

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.core.context import bind_institution
from apps.finance.models import FeeStructure, Invoice
from apps.institutions.models import Domain, Institution
from apps.permissions.models import (
    InstitutionMembership,
    MembershipRole,
    Permission,
    Role,
    RolePermission,
)
from apps.students.models import Enrollment, GuardianRelationship, Student

HOSTNAME = "st-mary.educore.africa"


class FinanceAPITestCase(APITestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        Domain.objects.create(
            institution=self.institution,
            hostname=HOSTNAME,
            domain_type=Domain.DomainType.SUBDOMAIN,
            is_primary=True,
        )
        self.user = User.objects.create_user(email="finance@stmary.ac.ke", password="x" * 12)
        self.membership = InstitutionMembership.objects.create(
            user=self.user, institution=self.institution
        )
        self.client.credentials(HTTP_AUTHORIZATION=self._bearer(self.user))

    def _bearer(self, user):
        return f"Bearer {RefreshToken.for_user(user).access_token}"

    def _grant(self, code, user=None, role_name=None):
        membership = self.membership
        if user is not None and user is not self.user:
            membership, _ = InstitutionMembership.objects.get_or_create(
                user=user, institution=self.institution
            )
        # Each call creates its own role — a test granting several
        # permission codes in one setUp (e.g. fee_structure.manage +
        # invoice.generate) must not collide on Role's
        # unique-name-per-institution constraint.
        role = Role.objects.create(
            name=role_name or f"Test Role — {code}", institution=self.institution
        )
        permission, _ = Permission.objects.get_or_create(code=code)
        RolePermission.objects.create(role=role, permission=permission)
        MembershipRole.objects.create(membership=membership, role=role)
        return role

    def _assign_role(self, role, user):
        membership, _ = InstitutionMembership.objects.get_or_create(
            user=user, institution=self.institution
        )
        MembershipRole.objects.create(membership=membership, role=role)


class FeeStructureViewSetTests(FinanceAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:finance:fee-structure-list")

    def test_create_without_permission_is_denied(self):
        response = self.client.post(
            self.url,
            {
                "class_grade_id": str(uuid.uuid4()),
                "term_id": str(uuid.uuid4()),
                "name": "Tuition",
                "line_items": [{"description": "Tuition", "amount": "1000.00"}],
            },
            format="json",
            HTTP_HOST=HOSTNAME,
        )
        self.assertEqual(response.status_code, 403)

    def test_create_computes_total_amount(self):
        self._grant("finance.fee_structure.manage")

        response = self.client.post(
            self.url,
            {
                "class_grade_id": str(uuid.uuid4()),
                "term_id": str(uuid.uuid4()),
                "name": "Tuition",
                "line_items": [
                    {"description": "Tuition", "amount": "800.00"},
                    {"description": "Activity", "amount": "200.00"},
                ],
            },
            format="json",
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["total_amount"], "1000.00")
        with bind_institution(self.institution):
            self.assertEqual(FeeStructure.objects.count(), 1)


class GenerateInvoicesActionTests(FinanceAPITestCase):
    def setUp(self):
        super().setUp()
        self._grant("finance.fee_structure.manage")
        self._grant("finance.invoice.generate")
        self.class_grade_id = uuid.uuid4()
        self.term_id = uuid.uuid4()
        create_response = self.client.post(
            reverse("v1:finance:fee-structure-list"),
            {
                "class_grade_id": str(self.class_grade_id),
                "term_id": str(self.term_id),
                "name": "Tuition",
                "line_items": [{"description": "Tuition", "amount": "1000.00"}],
            },
            format="json",
            HTTP_HOST=HOSTNAME,
        )
        self.fee_structure_id = create_response.data["id"]
        with bind_institution(self.institution):
            self.student = Student.objects.create(
                institution_id=self.institution.id,
                admission_number="ADM-001",
                first_name="Amina",
                last_name="Otieno",
            )
            Enrollment.objects.create(
                institution_id=self.institution.id,
                student=self.student,
                class_grade_id=self.class_grade_id,
                term_id=self.term_id,
            )

    def test_generates_one_invoice_per_actively_enrolled_student(self):
        url = reverse(
            "v1:finance:fee-structure-generate-invoices", kwargs={"pk": self.fee_structure_id}
        )

        response = self.client.post(url, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["created"], 1)
        with bind_institution(self.institution):
            invoice = Invoice.objects.get(student_id=self.student.id)
            self.assertEqual(str(invoice.amount_due), "1000.00")

    def test_creates_an_audit_log_entry(self):
        url = reverse(
            "v1:finance:fee-structure-generate-invoices", kwargs={"pk": self.fee_structure_id}
        )

        self.client.post(url, HTTP_HOST=HOSTNAME)

        self.assertTrue(
            AuditLog.objects.filter(action="finance.invoice.create", actor=self.user).exists()
        )


class InvoiceObjectScopeTests(FinanceAPITestCase):
    def setUp(self):
        super().setUp()
        with bind_institution(self.institution):
            self.child = Student.objects.create(
                institution_id=self.institution.id, admission_number="ADM-001", first_name="Amina",
                last_name="Otieno",
            )
            self.other_student = Student.objects.create(
                institution_id=self.institution.id, admission_number="ADM-002", first_name="Brian",
                last_name="Kamau",
            )
            self.invoice = Invoice.objects.create(
                institution_id=self.institution.id,
                student_id=self.child.id,
                term_id=uuid.uuid4(),
                amount_due="1000.00",
            )
            self.other_invoice = Invoice.objects.create(
                institution_id=self.institution.id,
                student_id=self.other_student.id,
                term_id=uuid.uuid4(),
                amount_due="500.00",
            )
            GuardianRelationship.objects.create(
                institution_id=self.institution.id,
                student=self.child,
                guardian_user_id=self.user.id,
                relationship_type=GuardianRelationship.RelationshipType.PARENT,
                is_primary_contact=True,
            )
        self.url = reverse("v1:finance:invoice-list")
        self._grant("finance.invoice.view", role_name="Parent")

    def test_parent_sees_only_their_own_childs_invoice(self):
        response = self.client.get(self.url, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 200)
        ids = {row["id"] for row in response.data["results"]}
        self.assertEqual(ids, {str(self.invoice.id)})


class PaymentIdempotencyTests(FinanceAPITestCase):
    def setUp(self):
        super().setUp()
        self._grant("finance.payment.record")
        with bind_institution(self.institution):
            self.invoice = Invoice.objects.create(
                institution_id=self.institution.id,
                student_id=uuid.uuid4(),
                term_id=uuid.uuid4(),
                amount_due="1000.00",
            )
        self.url = reverse("v1:finance:payment-list")

    def _payload(self):
        return {
            "invoice": str(self.invoice.id),
            "amount": "500.00",
            "method": "cash",
            "reference": "",
            "paid_at": "2026-01-05T10:00:00Z",
        }

    def test_replaying_the_same_idempotency_key_does_not_duplicate(self):
        headers = {"HTTP_HOST": HOSTNAME, "HTTP_IDEMPOTENCY_KEY": "req-1"}

        first = self.client.post(self.url, self._payload(), format="json", **headers)
        second = self.client.post(self.url, self._payload(), format="json", **headers)

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertEqual(first.data["id"], second.data["id"])
        with bind_institution(self.institution):
            self.assertEqual(self.invoice.payments.count(), 1)

    def test_different_idempotency_keys_both_record(self):
        headers_one = {"HTTP_HOST": HOSTNAME, "HTTP_IDEMPOTENCY_KEY": "req-1"}
        headers_two = {"HTTP_HOST": HOSTNAME, "HTTP_IDEMPOTENCY_KEY": "req-2"}
        self.client.post(self.url, self._payload(), format="json", **headers_one)
        self.client.post(self.url, self._payload(), format="json", **headers_two)

        with bind_institution(self.institution):
            self.assertEqual(self.invoice.payments.count(), 2)


class InitiateMpesaPaymentActionTests(FinanceAPITestCase):
    # base.py's default MPESA_GATEWAY_BACKEND is FakeMpesaGatewayBackend —
    # no network involved in any of these tests.

    def setUp(self):
        super().setUp()
        with bind_institution(self.institution):
            self.child = Student.objects.create(
                institution_id=self.institution.id,
                admission_number="ADM-001",
                first_name="Amina",
                last_name="Otieno",
            )
            self.invoice = Invoice.objects.create(
                institution_id=self.institution.id,
                student_id=self.child.id,
                term_id=uuid.uuid4(),
                amount_due="1000.00",
            )
            GuardianRelationship.objects.create(
                institution_id=self.institution.id,
                student=self.child,
                guardian_user_id=self.user.id,
                relationship_type=GuardianRelationship.RelationshipType.PARENT,
                is_primary_contact=True,
            )
        self.url = reverse(
            "v1:finance:invoice-initiate-mpesa-payment", kwargs={"pk": self.invoice.id}
        )

    def test_with_no_permission_or_role_is_denied(self):
        response = self.client.post(
            self.url, {"phone_number": "254712345678"}, format="json", HTTP_HOST=HOSTNAME
        )
        self.assertEqual(response.status_code, 403)

    def test_officer_path_requires_phone_number_in_body(self):
        self._grant("finance.payment.record")

        response = self.client.post(self.url, {}, format="json", HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 400)

    def test_officer_path_uses_the_body_supplied_phone_number(self):
        self._grant("finance.payment.record")

        response = self.client.post(
            self.url, {"phone_number": "254798765432"}, format="json", HTTP_HOST=HOSTNAME
        )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data["phone_number"], "254798765432")
        self.assertEqual(response.data["status"], "pending")

    def test_parent_path_uses_their_own_profile_phone_never_the_body(self):
        self.user.phone = "254711223344"
        self.user.save(update_fields=["phone"])
        self._grant("finance.invoice.view", role_name="Parent")

        response = self.client.post(
            # Attempting to override with someone else's number — must be ignored.
            self.url,
            {"phone_number": "254700000000"},
            format="json",
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data["phone_number"], "254711223344")

    def test_parent_path_without_a_phone_on_file_is_rejected(self):
        self._grant("finance.invoice.view", role_name="Parent")

        response = self.client.post(self.url, {}, format="json", HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 400)

    def test_parent_cannot_initiate_for_another_students_invoice(self):
        with bind_institution(self.institution):
            other_student = Student.objects.create(
                institution_id=self.institution.id,
                admission_number="ADM-002",
                first_name="Brian",
                last_name="Kamau",
            )
            other_invoice = Invoice.objects.create(
                institution_id=self.institution.id,
                student_id=other_student.id,
                term_id=uuid.uuid4(),
                amount_due="500.00",
            )
        self.user.phone = "254711223344"
        self.user.save(update_fields=["phone"])
        self._grant("finance.invoice.view", role_name="Parent")
        url = reverse(
            "v1:finance:invoice-initiate-mpesa-payment", kwargs={"pk": other_invoice.id}
        )

        response = self.client.post(url, {}, format="json", HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 404)

    def test_rate_limit_trips_after_the_configured_ceiling(self):
        self._grant("finance.payment.record")

        responses = [
            self.client.post(
                self.url, {"phone_number": "254712345678"}, format="json", HTTP_HOST=HOSTNAME
            )
            for _ in range(6)
        ]

        self.assertEqual([r.status_code for r in responses[:5]], [202] * 5)
        self.assertEqual(responses[5].status_code, 429)


class PayrollViewSetTests(FinanceAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:finance:payroll-record-list")

    def _payload(self, staff_id=None, period="2026-01-01"):
        return {
            "staff_id": str(staff_id or uuid.uuid4()),
            "period": period,
            "gross": "50000.00",
            "deductions": [{"description": "PAYE", "amount": "8000.00"}],
            "paid_at": "2026-01-31T10:00:00Z",
        }

    def test_create_without_permission_is_denied(self):
        response = self.client.post(self.url, self._payload(), format="json", HTTP_HOST=HOSTNAME)
        self.assertEqual(response.status_code, 403)

    def test_create_computes_net(self):
        self._grant("finance.payroll.manage")

        response = self.client.post(self.url, self._payload(), format="json", HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["net"], "42000.00")

    def test_read_requires_view_permission(self):
        self._grant("finance.payroll.manage")
        self.client.post(self.url, self._payload(), format="json", HTTP_HOST=HOSTNAME)

        # The manage grant above doesn't include view — reads are gated
        # separately (docs/permissions.md §5's view/manage split).
        response = self.client.get(self.url, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 403)

    def test_filters_by_staff(self):
        self._grant("finance.payroll.manage")
        self._grant("finance.payroll.view")
        staff_id = uuid.uuid4()
        self.client.post(
            self.url, self._payload(staff_id=staff_id), format="json", HTTP_HOST=HOSTNAME
        )
        self.client.post(self.url, self._payload(), format="json", HTTP_HOST=HOSTNAME)

        response = self.client.get(self.url, {"staff": str(staff_id)}, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["staff_id"], str(staff_id))


class ExpenseRecordViewSetTests(FinanceAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:finance:expense-record-list")

    def _payload(self, category="Utilities"):
        return {"category": category, "amount": "2500.00", "incurred_at": "2026-01-05"}

    def test_create_without_permission_is_denied(self):
        response = self.client.post(self.url, self._payload(), format="json", HTTP_HOST=HOSTNAME)
        self.assertEqual(response.status_code, 403)

    def test_create_injects_the_approver_from_the_authenticated_user(self):
        self._grant("finance.expense_record.manage")

        response = self.client.post(self.url, self._payload(), format="json", HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["approved_by_id"], str(self.user.id))

    def test_filters_by_category(self):
        self._grant("finance.expense_record.manage")
        self._grant("finance.expense_record.view")
        self.client.post(self.url, self._payload("Utilities"), format="json", HTTP_HOST=HOSTNAME)
        self.client.post(self.url, self._payload("Transport"), format="json", HTTP_HOST=HOSTNAME)

        response = self.client.get(self.url, {"category": "Transport"}, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["category"], "Transport")

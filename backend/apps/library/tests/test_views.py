import uuid

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.core.context import bind_institution
from apps.institutions.models import Domain, Institution
from apps.library.models import Book, Copy, Loan
from apps.permissions.models import (
    InstitutionMembership,
    MembershipRole,
    Permission,
    Role,
    RolePermission,
)

HOSTNAME = "st-mary.educore.africa"


class LibraryAPITestCase(APITestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        Domain.objects.create(
            institution=self.institution,
            hostname=HOSTNAME,
            domain_type=Domain.DomainType.SUBDOMAIN,
            is_primary=True,
        )
        self.user = User.objects.create_user(email="librarian@stmary.ac.ke", password="x" * 12)
        self.membership = InstitutionMembership.objects.create(
            user=self.user, institution=self.institution
        )
        self.client.credentials(HTTP_AUTHORIZATION=self._bearer(self.user))
        with bind_institution(self.institution):
            self.book = Book.objects.create(institution_id=self.institution.id, title="Emma")
            self.copy = Copy.objects.create(
                institution_id=self.institution.id, book=self.book, barcode="BC-1"
            )

    def _bearer(self, user):
        return f"Bearer {RefreshToken.for_user(user).access_token}"

    def _grant(self, code):
        role = Role.objects.create(name="Test Role", institution=self.institution)
        permission = Permission.objects.create(code=code)
        RolePermission.objects.create(role=role, permission=permission)
        MembershipRole.objects.create(membership=self.membership, role=role)


class LoanViewSetTests(LibraryAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:library:loan-list")

    def test_checkout_without_permission_is_denied(self):
        response = self.client.post(
            self.url,
            {
                "copy": str(self.copy.id),
                "borrower_type": "student",
                "borrower_id": str(uuid.uuid4()),
                "due_date": "2026-02-01",
            },
            HTTP_HOST=HOSTNAME,
        )
        self.assertEqual(response.status_code, 403)

    def test_checkout_with_permission_creates_a_loan_and_marks_the_copy_on_loan(self):
        self._grant("library.loan.manage")

        response = self.client.post(
            self.url,
            {
                "copy": str(self.copy.id),
                "borrower_type": "student",
                "borrower_id": str(uuid.uuid4()),
                "due_date": "2026-02-01",
            },
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)
        self.copy.refresh_from_db()
        self.assertEqual(self.copy.status, Copy.Status.ON_LOAN)

    def test_checkout_of_an_unavailable_copy_is_rejected(self):
        self._grant("library.loan.manage")
        payload = {
            "copy": str(self.copy.id),
            "borrower_type": "student",
            "borrower_id": str(uuid.uuid4()),
            "due_date": "2026-02-01",
        }
        self.client.post(self.url, payload, HTTP_HOST=HOSTNAME)

        response = self.client.post(
            self.url,
            {**payload, "borrower_id": str(uuid.uuid4())},
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 400)

    def test_return_loan_marks_it_returned_and_the_copy_available(self):
        self._grant("library.loan.manage")
        checkout_response = self.client.post(
            self.url,
            {
                "copy": str(self.copy.id),
                "borrower_type": "student",
                "borrower_id": str(uuid.uuid4()),
                "due_date": "2026-02-01",
            },
            HTTP_HOST=HOSTNAME,
        )
        loan_id = checkout_response.data["id"]

        response = self.client.post(
            reverse("v1:library:loan-return", kwargs={"pk": loan_id}),
            {},
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data["returned_at"])
        self.copy.refresh_from_db()
        self.assertEqual(self.copy.status, Copy.Status.AVAILABLE)

    def test_return_loan_without_permission_is_denied(self):
        self._grant("library.loan.manage")
        checkout_response = self.client.post(
            self.url,
            {
                "copy": str(self.copy.id),
                "borrower_type": "student",
                "borrower_id": str(uuid.uuid4()),
                "due_date": "2026-02-01",
            },
            HTTP_HOST=HOSTNAME,
        )
        loan_id = checkout_response.data["id"]
        # Revoke by starting a fresh, permission-less client instead of
        # unwinding the granted role.
        other_user = User.objects.create_user(email="teacher@stmary.ac.ke", password="x" * 12)
        InstitutionMembership.objects.create(user=other_user, institution=self.institution)
        self.client.credentials(HTTP_AUTHORIZATION=self._bearer(other_user))

        response = self.client.post(
            reverse("v1:library:loan-return", kwargs={"pk": loan_id}),
            {},
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 403)

    def test_filter_by_returned(self):
        self._grant("library.loan.manage")
        with bind_institution(self.institution):
            other_copy = Copy.objects.create(
                institution_id=self.institution.id, book=self.book, barcode="BC-2"
            )
            Loan.objects.create(
                institution_id=self.institution.id,
                copy=self.copy,
                borrower_type="student",
                borrower_id=uuid.uuid4(),
                due_date="2026-02-01",
            )
            Loan.objects.create(
                institution_id=self.institution.id,
                copy=other_copy,
                borrower_type="student",
                borrower_id=uuid.uuid4(),
                due_date="2026-02-01",
                returned_at="2026-01-15T00:00:00+00:00",
            )

        response = self.client.get(self.url, {"returned": "false"}, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)


class BookViewSetTests(LibraryAPITestCase):
    def test_reads_are_open_to_any_active_member(self):
        response = self.client.get(reverse("v1:library:book-list"), HTTP_HOST=HOSTNAME)
        self.assertEqual(response.status_code, 200)

    def test_create_without_permission_is_denied(self):
        response = self.client.post(
            reverse("v1:library:book-list"), {"title": "Dune"}, HTTP_HOST=HOSTNAME
        )
        self.assertEqual(response.status_code, 403)

    def test_create_with_permission_succeeds(self):
        self._grant("library.book.manage")
        response = self.client.post(
            reverse("v1:library:book-list"), {"title": "Dune"}, HTTP_HOST=HOSTNAME
        )
        self.assertEqual(response.status_code, 201)

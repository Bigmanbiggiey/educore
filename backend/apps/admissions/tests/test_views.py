import uuid

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.admissions.models import Application
from apps.core.context import bind_institution
from apps.institutions.models import Domain, Institution
from apps.permissions.models import (
    InstitutionMembership,
    MembershipRole,
    Permission,
    Role,
    RolePermission,
)

HOSTNAME = "st-mary.educore.africa"


class AdmissionsAPITestCase(APITestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        Domain.objects.create(
            institution=self.institution,
            hostname=HOSTNAME,
            domain_type=Domain.DomainType.SUBDOMAIN,
            is_primary=True,
        )
        self.user = User.objects.create_user(email="staff@stmary.ac.ke", password="x" * 12)
        self.membership = InstitutionMembership.objects.create(
            user=self.user, institution=self.institution
        )
        self.url = reverse("v1:admissions:application-list")

    def _bearer(self, user):
        return f"Bearer {RefreshToken.for_user(user).access_token}"

    def _authenticate(self):
        self.client.credentials(HTTP_AUTHORIZATION=self._bearer(self.user))

    def _grant(self, code):
        role = Role.objects.create(name="Test Role", institution=self.institution)
        permission = Permission.objects.create(code=code)
        RolePermission.objects.create(role=role, permission=permission)
        MembershipRole.objects.create(membership=self.membership, role=role)


class SubmitApplicationTests(AdmissionsAPITestCase):
    def test_an_anonymous_applicant_can_submit(self):
        response = self.client.post(
            self.url,
            {
                "applicant_details": {"first_name": "Amina", "last_name": "Otieno"},
                "term_applying_for_id": str(uuid.uuid4()),
            },
            format="json",
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["stage"], "submitted")
        with bind_institution(self.institution):
            self.assertEqual(Application.objects.count(), 1)

    def test_list_requires_authentication(self):
        response = self.client.get(self.url, HTTP_HOST=HOSTNAME)
        self.assertEqual(response.status_code, 401)


class ApplicationLifecycleActionTests(AdmissionsAPITestCase):
    def setUp(self):
        super().setUp()
        submit_response = self.client.post(
            self.url,
            {
                "applicant_details": {"first_name": "Amina", "last_name": "Otieno"},
                "term_applying_for_id": str(uuid.uuid4()),
            },
            format="json",
            HTTP_HOST=HOSTNAME,
        )
        self.application_id = submit_response.data["id"]
        self.make_offer_url = reverse(
            "v1:admissions:application-make-offer", kwargs={"pk": self.application_id}
        )
        self.accept_offer_url = reverse(
            "v1:admissions:application-accept-offer", kwargs={"pk": self.application_id}
        )
        self.convert_url = reverse(
            "v1:admissions:application-convert-to-enrollment", kwargs={"pk": self.application_id}
        )

    def test_make_offer_requires_permission(self):
        self._authenticate()
        response = self.client.post(self.make_offer_url, HTTP_HOST=HOSTNAME)
        self.assertEqual(response.status_code, 403)

    def test_full_lifecycle_over_http(self):
        self._authenticate()
        self._grant("admissions.application.manage")

        offer_response = self.client.post(self.make_offer_url, HTTP_HOST=HOSTNAME)
        self.assertEqual(offer_response.status_code, 201)

        accept_response = self.client.post(self.accept_offer_url, HTTP_HOST=HOSTNAME)
        self.assertEqual(accept_response.status_code, 200)
        self.assertIsNotNone(accept_response.data["accepted_at"])

        convert_response = self.client.post(
            self.convert_url,
            {
                "admission_number": "ADM-001",
                "class_grade_id": str(uuid.uuid4()),
                "term_id": str(uuid.uuid4()),
            },
            format="json",
            HTTP_HOST=HOSTNAME,
        )
        self.assertEqual(convert_response.status_code, 201)
        self.assertIn("enrollment_id", convert_response.data)

    def test_convert_before_accept_is_rejected(self):
        self._authenticate()
        self._grant("admissions.application.manage")
        self.client.post(self.make_offer_url, HTTP_HOST=HOSTNAME)

        response = self.client.post(
            self.convert_url,
            {
                "admission_number": "ADM-001",
                "class_grade_id": str(uuid.uuid4()),
                "term_id": str(uuid.uuid4()),
            },
            format="json",
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 400)

    def test_accept_offer_without_an_offer_is_rejected(self):
        self._authenticate()
        self._grant("admissions.application.manage")

        response = self.client.post(self.accept_offer_url, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 400)

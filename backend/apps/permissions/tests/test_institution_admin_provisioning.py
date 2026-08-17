"""End-to-end integration test for the real (unmocked) signal chain
`apps.institutions.services.provision_institution` -> `core.signals.institution_provisioned`
-> `apps.permissions.receivers` -> `apps.permissions.services.provision_institution_admin`,
triggered via a genuine HTTP request to the platform-staff institution
provisioning endpoint. Lives in `apps.permissions.tests` (not
`apps.institutions.tests`) since it needs both `apps.institutions` and
`apps.accounts` models — the one Layer 0 app allowed to import both,
per `.importlinter`.
"""

from unittest.mock import patch

from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.models import User
from apps.institutions.models import Institution
from apps.permissions.models import InstitutionMembership, MembershipRole, Role

PLATFORM_HOST = "admin.educore.africa"
_THROTTLING_DISABLED = {**settings.REST_FRAMEWORK, "DEFAULT_THROTTLE_CLASSES": []}


@override_settings(REST_FRAMEWORK=_THROTTLING_DISABLED)
class InstitutionAdminProvisioningIntegrationTests(APITestCase):
    def setUp(self):
        self.platform_staff = User.objects.create_user(
            email="platform@educore.africa", password="x" * 12, is_platform_staff=True
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(self.platform_staff)}"
        )
        self.url = reverse("v1:institutions:institution-list")

    @patch("apps.notifications_core.services.dispatch_notification.delay")
    def test_provisioning_an_institution_creates_its_administrator_end_to_end(self, mock_delay):
        response = self.client.post(
            self.url,
            {
                "name": "St Mary",
                "slug": "st-mary",
                "curriculum_types": ["cbc"],
                "admin_email": "admin@stmary.ac.ke",
            },
            HTTP_HOST=PLATFORM_HOST,
        )

        self.assertEqual(response.status_code, 201, response.data)
        institution = Institution.objects.get(slug="st-mary")
        admin_user = User.objects.get(email="admin@stmary.ac.ke")
        membership = InstitutionMembership.objects.get(user=admin_user, institution=institution)
        self.assertTrue(membership.is_default)
        self.assertTrue(
            MembershipRole.objects.filter(
                membership=membership,
                role=Role.objects.get(name="Institution Administrator", institution__isnull=True),
            ).exists()
        )
        mock_delay.assert_called_once()

    def test_non_platform_staff_cannot_provision_an_institution(self):
        regular_user = User.objects.create_user(email="teacher@stmary.ac.ke", password="x" * 12)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(regular_user)}"
        )

        response = self.client.post(
            self.url,
            {
                "name": "St Mary",
                "slug": "st-mary",
                "curriculum_types": ["cbc"],
                "admin_email": "admin@stmary.ac.ke",
            },
            HTTP_HOST=PLATFORM_HOST,
        )

        self.assertEqual(response.status_code, 403)

    def test_missing_admin_email_is_rejected(self):
        response = self.client.post(
            self.url,
            {"name": "St Mary", "slug": "st-mary", "curriculum_types": ["cbc"]},
            HTTP_HOST=PLATFORM_HOST,
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("admin_email", response.data["error"]["fields"])

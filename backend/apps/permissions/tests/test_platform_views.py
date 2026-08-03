from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.accounts.models import User

PLATFORM_HOST = "admin.educore.africa"

# Same throttling-disable pattern apps.permissions.tests.test_views already
# uses for its AuthViewTestCase base — login endpoints share one IP-keyed
# anon-throttle bucket (docs/api-design.md §13's 5/min default), and
# throttling itself isn't what's under test here.
_THROTTLING_DISABLED = {**settings.REST_FRAMEWORK, "DEFAULT_THROTTLE_CLASSES": []}


@override_settings(REST_FRAMEWORK=_THROTTLING_DISABLED)
class HostContextViewTests(APITestCase):
    def test_platform_host_reports_platform(self):
        response = self.client.get(
            reverse("v1:permissions:host-context"), HTTP_HOST=PLATFORM_HOST
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["host_type"], "platform")


@override_settings(REST_FRAMEWORK=_THROTTLING_DISABLED)
class PlatformLoginViewTests(APITestCase):
    def setUp(self):
        self.url = reverse("v1:permissions-platform:platform-login")
        self.staff_user = User.objects.create_user(
            email="admin@educore.africa", password="a-decent-password", is_platform_staff=True
        )
        self.regular_user = User.objects.create_user(
            email="teacher@stmary.ac.ke", password="a-decent-password"
        )

    def test_platform_staff_can_log_in(self):
        response = self.client.post(
            self.url,
            {"email_or_phone": "admin@educore.africa", "password": "a-decent-password"},
            HTTP_HOST=PLATFORM_HOST,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.data)

    def test_wrong_password_is_rejected(self):
        response = self.client.post(
            self.url,
            {"email_or_phone": "admin@educore.africa", "password": "wrong"},
            HTTP_HOST=PLATFORM_HOST,
        )
        self.assertEqual(response.status_code, 401)

    def test_non_platform_staff_user_is_rejected_even_with_the_right_password(self):
        response = self.client.post(
            self.url,
            {"email_or_phone": "teacher@stmary.ac.ke", "password": "a-decent-password"},
            HTTP_HOST=PLATFORM_HOST,
        )
        self.assertEqual(response.status_code, 401)

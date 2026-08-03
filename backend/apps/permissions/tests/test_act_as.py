from django.conf import settings
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.institutions.models import Domain, Institution

PLATFORM_HOST = "admin.educore.africa"

# Same throttling-disable pattern apps.permissions.tests.test_views already
# uses — irrelevant to what's under test here.
_THROTTLING_DISABLED = {**settings.REST_FRAMEWORK, "DEFAULT_THROTTLE_CLASSES": []}


@override_settings(REST_FRAMEWORK=_THROTTLING_DISABLED)
class ActAsTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        Domain.objects.create(
            institution=self.institution,
            hostname="st-mary.educore.africa",
            domain_type=Domain.DomainType.SUBDOMAIN,
            is_primary=True,
        )
        self.platform_user = User.objects.create_user(
            email="admin@educore.africa", password="x" * 12, is_platform_staff=True
        )
        self.students_url = reverse("v1:students:student-list")
        self.act_as_url = reverse(
            "v1:permissions-platform:act-as", kwargs={"institution_id": self.institution.id}
        )
        self.act_as_end_url = reverse("v1:permissions-platform:act-as-end")

    def _bearer(self, token):
        return f"Bearer {token}"

    def _platform_bearer(self):
        return self._bearer(AccessToken.for_user(self.platform_user))

    def _start_act_as(self):
        self.client.credentials(HTTP_AUTHORIZATION=self._platform_bearer())
        response = self.client.post(self.act_as_url, HTTP_HOST=PLATFORM_HOST)
        self.assertEqual(response.status_code, 200)
        return response.data["access_token"]

    def test_regular_authenticated_user_cannot_start_a_break_glass_session(self):
        regular_user = User.objects.create_user(email="teacher@stmary.ac.ke", password="x" * 12)
        self.client.credentials(HTTP_AUTHORIZATION=self._bearer(AccessToken.for_user(regular_user)))

        response = self.client.post(self.act_as_url, HTTP_HOST=PLATFORM_HOST)

        self.assertEqual(response.status_code, 403)

    def test_starting_a_session_is_audited(self):
        self._start_act_as()

        log = AuditLog.objects.get(action="platform.admin.impersonate_start")
        self.assertEqual(log.actor, self.platform_user)
        self.assertEqual(log.institution, self.institution)
        self.assertTrue(log.acting_as_admin)

    def test_elevated_token_grants_temporary_access_to_the_named_institution(self):
        elevated_token = self._start_act_as()

        self.client.credentials(HTTP_AUTHORIZATION=self._bearer(elevated_token))
        response = self.client.get(self.students_url, HTTP_HOST=PLATFORM_HOST)

        self.assertEqual(response.status_code, 200)

    def test_elevated_token_does_not_work_on_a_normal_institution_host(self):
        # The whole point of the break-glass design is that the System
        # Admin never leaves admin.educore.africa — the elevated token
        # only means anything there.
        elevated_token = self._start_act_as()

        self.client.credentials(HTTP_AUTHORIZATION=self._bearer(elevated_token))
        response = self.client.get(self.students_url, HTTP_HOST="st-mary.educore.africa")

        self.assertEqual(response.status_code, 403)

    def test_creating_a_student_while_acting_as_admin_is_audited(self):
        elevated_token = self._start_act_as()
        self.client.credentials(HTTP_AUTHORIZATION=self._bearer(elevated_token))

        response = self.client.post(
            self.students_url,
            {"admission_number": "A-100", "first_name": "Jane", "last_name": "Doe"},
            HTTP_HOST=PLATFORM_HOST,
        )

        self.assertEqual(response.status_code, 201)
        log = AuditLog.objects.get(action="students.student.create")
        self.assertTrue(log.acting_as_admin)
        self.assertEqual(log.actor, self.platform_user)

    def test_ending_the_session_immediately_revokes_the_elevated_token(self):
        elevated_token = self._start_act_as()

        self.client.credentials(HTTP_AUTHORIZATION=self._bearer(elevated_token))
        end_response = self.client.post(self.act_as_end_url, HTTP_HOST=PLATFORM_HOST)
        self.assertEqual(end_response.status_code, 200)

        end_log = AuditLog.objects.get(action="platform.admin.impersonate_end")
        self.assertTrue(end_log.acting_as_admin)

        # Same token, still cryptographically valid and unexpired — but the
        # explicit-exit revocation flag must block institution binding now.
        response = self.client.get(self.students_url, HTTP_HOST=PLATFORM_HOST)
        self.assertEqual(response.status_code, 403)

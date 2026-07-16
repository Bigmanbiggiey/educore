from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings

from apps.core.context import current_institution
from apps.institutions.middleware import TenantMiddleware
from apps.institutions.models import Domain, Institution


class TenantMiddlewareTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        Domain.objects.create(
            institution=self.institution,
            hostname="st-mary.educore.africa",
            domain_type=Domain.DomainType.SUBDOMAIN,
            is_primary=True,
        )

    def _middleware(self, seen):
        def get_response(request):
            seen["institution"] = getattr(request, "institution", None)
            seen["ctx_during_request"] = current_institution.get()
            return HttpResponse()

        return TenantMiddleware(get_response)

    def test_binds_the_resolved_institution_for_a_known_host(self):
        seen = {}
        middleware = self._middleware(seen)
        request = RequestFactory().get("/", HTTP_HOST="st-mary.educore.africa")

        middleware(request)

        self.assertEqual(seen["institution"], self.institution)
        self.assertEqual(seen["ctx_during_request"], self.institution)
        # Reset after the request — must not leak into the next one handled
        # by the same worker (docs/multitenancy.md §2).
        self.assertIsNone(current_institution.get())

    def test_404s_for_an_unrecognized_host(self):
        middleware = self._middleware({})
        request = RequestFactory().get("/", HTTP_HOST="nope.educore.africa")

        response = middleware(request)

        self.assertEqual(response.status_code, 404)

    @override_settings(PLATFORM_HOSTS=["admin.educore.africa"])
    def test_platform_hosts_bypass_tenant_resolution(self):
        seen = {}
        middleware = self._middleware(seen)
        request = RequestFactory().get("/", HTTP_HOST="admin.educore.africa")

        response = middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(seen["institution"])

    def test_healthz_bypasses_tenant_resolution_regardless_of_host(self):
        seen = {}
        middleware = self._middleware(seen)
        request = RequestFactory().get("/healthz/", HTTP_HOST="nope.educore.africa")

        response = middleware(request)

        self.assertEqual(response.status_code, 200)

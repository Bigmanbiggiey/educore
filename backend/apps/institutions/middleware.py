"""TenantMiddleware — resolves the request's tenant from the Host header
and binds it for the request's duration (docs/multitenancy.md §2).
"""

from django.conf import settings
from django.http import HttpResponseNotFound

from apps.core.context import bind_institution
from apps.institutions.selectors import get_institution_by_domain

# Infra endpoints that must answer regardless of tenant resolution (an
# uptime monitor or Docker healthcheck has no institution context to send).
EXEMPT_PATH_PREFIXES = ("/healthz/",)


class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith(EXEMPT_PATH_PREFIXES):
            return self.get_response(request)

        host = request.get_host().split(":")[0]
        if host in settings.PLATFORM_HOSTS:
            # e.g. admin.educore.africa — platform-staff traffic, no
            # institution context set.
            return self.get_response(request)

        institution = get_institution_by_domain(host)
        if institution is None:
            return HttpResponseNotFound()

        request.institution = institution
        with bind_institution(institution):
            return self.get_response(request)

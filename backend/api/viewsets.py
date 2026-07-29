"""Shared ViewSet base for every Layer 1+ app (docs/roadmap.md Phase 2
onward) — docs/api-design.md §7: there is no `institution_id` parameter
anywhere in the API, so every tenant-scoped create must inject it from
`request.institution` (set by `TenantMiddleware`) rather than trusting
anything in the request body.

Subclasses set `queryset_model`, not DRF's usual class-level `queryset` —
`TenantManager.get_queryset()` (apps.core.models) raises `TenantContextMissing`
*eagerly*, the moment `.all()`/`.filter()` is called, not lazily at
iteration (verified/intentional per `apps.core.tests.test_models`). A
class-level `queryset = Model.objects.all()` attribute is evaluated once at
class-body/import time — long before any request (and the tenant
`TenantMiddleware` binds for it) exists — so it would raise on Django
startup, before serving a single request. `get_queryset` below resolves
`queryset_model.objects.all()` fresh on every call instead, by which point
a request (and its bound tenant) is always in progress — the standard DRF
pattern for any per-request-dynamic queryset.
"""

from rest_framework import viewsets


class TenantScopedModelViewSet(viewsets.ModelViewSet):
    queryset_model = None

    def get_base_queryset(self):
        """The full tenant-scoped queryset for `queryset_model`. Subclasses
        that need extra queryset-level filtering (e.g. an object-scope
        restriction per docs/permissions.md §3 — a Parent scoped to their
        own children, a Student to their own record) should override
        `get_queryset` to further `.filter()` *this*, rather than
        reimplementing the `swagger_fake_view` handling themselves."""
        if getattr(self, "swagger_fake_view", False):
            # drf-spectacular's schema generation calls this with no real
            # request (and so no bound tenant) in progress — DRF's own
            # documented escape hatch for this exact situation. `.objects`
            # would raise the same as above; `all_tenants_unsafe` is safe
            # to use here specifically because this never runs against a
            # real request (docs/multitenancy.md §3) — there's no tenant
            # to leak across, only a placeholder queryset for type
            # introspection.
            return self.queryset_model.all_tenants_unsafe.none()
        return self.queryset_model.objects.all()

    def get_queryset(self):
        return self.get_base_queryset()

    def perform_create(self, serializer):
        serializer.save(institution_id=self.request.institution.id)

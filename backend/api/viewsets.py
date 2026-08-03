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

Also binds `apps.core.context.current_user` for the span of the request
(`initial()` through `finalize_response()`) — `TenantMiddleware` can't do
this itself, since it runs before DRF authentication resolves `request.user`
(docs/authentication.md §6). This is what makes `apps.finance.signals`'
audit-signal wiring able to attribute a write to its actor without every
call site threading a user through explicitly.

`TenantScopedReadOnlyModelViewSet` (Phase 8, `analytics`) shares everything
above except `perform_create` — for machine-written data (Celery-computed
rollups) that has no client-facing write path at all, not even the
generic tenant-scoped one.
"""

from rest_framework import viewsets

from apps.audit.services import log_action
from apps.core.context import current_user


class TenantScopedViewSetMixin:
    queryset_model = None

    def _log_write_if_acting_as_admin(self, verb: str, instance) -> None:
        """docs/permissions.md §7: every write taken during a break-glass
        act-as session is audited with `acting_as_admin=True`, regardless
        of which app's viewset made it — generic here rather than
        threaded through every app's `views.py` individually. This module
        lives outside `apps.*` (`root_package = apps` in `.importlinter`),
        so it's the one place that can import `apps.audit` directly
        without tripping the Layer 0 sibling-independence contract that
        blocks e.g. `apps.permissions` from doing the same.

        Known, stated gap: viewsets with a fully custom `create()` that
        never calls `perform_create` (`library.LoanViewSet`,
        `finance.PaymentViewSet`, `hostel.BedAllocationViewSet`, a few
        others) don't route through here — not worth threading manual
        logging into each one for this pass.
        """
        if not getattr(self.request, "acting_as_admin", False):
            return
        meta = instance._meta
        log_action(
            actor=self.request.user if self.request.user.is_authenticated else None,
            institution=getattr(self.request, "institution", None),
            action=f"{meta.app_label}.{meta.model_name}.{verb}",
            target=instance,
            acting_as_admin=True,
        )

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        actor = request.user if request.user.is_authenticated else None
        self._actor_token = current_user.set(actor)

    def finalize_response(self, request, response, *args, **kwargs):
        token = getattr(self, "_actor_token", None)
        if token is not None:
            current_user.reset(token)
        return super().finalize_response(request, response, *args, **kwargs)

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


class TenantScopedModelViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    def perform_create(self, serializer):
        serializer.save(institution_id=self.request.institution.id)
        self._log_write_if_acting_as_admin("create", serializer.instance)

    def perform_update(self, serializer):
        serializer.save()
        self._log_write_if_acting_as_admin("update", serializer.instance)

    def perform_destroy(self, instance):
        self._log_write_if_acting_as_admin("destroy", instance)
        instance.delete()


class TenantScopedReadOnlyModelViewSet(TenantScopedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    pass

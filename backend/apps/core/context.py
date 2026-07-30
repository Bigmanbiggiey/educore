"""Tenant context primitives — see docs/multitenancy.md §2-3.

Uses contextvars, not thread-locals, because a thread (or Celery worker
process) can be reused across unrelated requests/tasks; contextvars are
copied safely per async task and explicitly reset in a `finally`, so
nothing leaks into the next request or task sharing the same worker.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.accounts.models import User
    from apps.institutions.models import Institution

current_institution: ContextVar[Institution | None] = ContextVar(
    "current_institution", default=None
)

# Set by CorrelationIdMiddleware so structured logging (docs/architecture.md
# §6) can attach the current request's correlation ID to every log line
# without every call site threading it through explicitly.
correlation_id_ctx: ContextVar[str | None] = ContextVar("correlation_id", default=None)

# Bound by api.viewsets.TenantScopedModelViewSet for the duration of a
# request, once request.user is known — not by TenantMiddleware, since
# TenantMiddleware runs before authentication (docs/authentication.md §6).
# Consumed by audit-signal wiring (first real consumer: apps.finance.signals,
# docs/checklist.md's "Audit-log signals confirmed firing on every finance
# write") so a signal handler can attribute a write to its actor without
# every call site threading a user through explicitly.
current_user: ContextVar[User | None] = ContextVar("current_user", default=None)


class TenantContextMissing(Exception):
    """Raised when tenant-scoped code runs with no institution bound.

    Fails loudly by design (docs/multitenancy.md §3) rather than silently
    returning an unfiltered or empty queryset.
    """


@contextmanager
def bind_institution(institution: Institution) -> Iterator[None]:
    """Bind `institution` as the current tenant for the duration of the
    block, resetting on exit even if the block raises.

    `TenantMiddleware` (apps.institutions) and the Celery tenant-aware task
    decorator are the two real call sites; this exists so both share one
    set/reset discipline instead of duplicating it.
    """
    token = current_institution.set(institution)
    try:
        yield
    finally:
        current_institution.reset(token)


@contextmanager
def bind_actor(user: User | None) -> Iterator[None]:
    """Bind `user` as the current actor for the duration of the block —
    same set/reset-in-a-finally discipline as `bind_institution`. The one
    real call site is `api.viewsets.TenantScopedModelViewSet`; tests/Celery
    tasks with no authenticated user simply don't bind one, leaving
    `current_user.get()` at its `None` default (audit rows already allow a
    null actor for system/Celery-initiated actions, docs/database.md §2)."""
    token = current_user.set(user)
    try:
        yield
    finally:
        current_user.reset(token)

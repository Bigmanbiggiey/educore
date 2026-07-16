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
    from apps.institutions.models import Institution

current_institution: ContextVar[Institution | None] = ContextVar(
    "current_institution", default=None
)

# Set by CorrelationIdMiddleware so structured logging (docs/architecture.md
# §6) can attach the current request's correlation ID to every log line
# without every call site threading it through explicitly.
correlation_id_ctx: ContextVar[str | None] = ContextVar("correlation_id", default=None)


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

"""Idempotency-Key support for client-initiated finance writes —
docs/api-design.md §11: "Client-initiated finance writes (manual cash/bank
entry) accept an optional `Idempotency-Key` header; the response for a
given key is cached and replayed rather than the operation re-executing."

This is additive: a request with no `Idempotency-Key` header behaves
exactly as it always has (`replay_or_execute` just calls `fn()` directly,
no caching involved) — no existing endpoint's behavior changes by this
module existing. `apps.finance.views.PaymentViewSet` is the first, and so
far only, caller (manual cash/bank payment entry is the one write this
project's docs call out by name; the M-Pesa callback's own idempotency is
a separate mechanism — upserting on M-Pesa's `TransactionID` — added in a
later stage, not this header).

Backed by the same Redis cache every DRF throttle counter already uses
(`CACHES["default"]`, `django_redis`) — no new infra.
"""

from __future__ import annotations

import pickle
from collections.abc import Callable
from typing import TypeVar

from django.core.cache import cache
from rest_framework.response import Response

_T = TypeVar("_T", bound=Response)

IDEMPOTENCY_KEY_HEADER = "Idempotency-Key"
_TTL_SECONDS = 60 * 60 * 24  # 24h — long enough to cover any realistic client retry window.


def replay_or_execute(request, *, scope: str, institution_id, fn: Callable[[], _T]) -> _T:
    """If `request` carries an `Idempotency-Key` header and a cached response
    exists for `(institution_id, scope, key)`, return it unexecuted.
    Otherwise call `fn()`, cache the result, and return it. `scope` namespaces
    keys per endpoint (e.g. "finance.payment.record") so two different
    write endpoints can't collide on a client-chosen key.
    """
    key = request.headers.get(IDEMPOTENCY_KEY_HEADER)
    if not key:
        return fn()

    cache_key = f"idempotency:{institution_id}:{scope}:{key}"
    cached = cache.get(cache_key)
    if cached is not None:
        status_code, data = pickle.loads(cached)
        return Response(data, status=status_code)

    response = fn()
    # Only cache genuinely successful writes — a validation/permission
    # error should still be retriable with the same key, not permanently
    # frozen as the replayed outcome.
    if 200 <= response.status_code < 300:
        cache.set(cache_key, pickle.dumps((response.status_code, response.data)), _TTL_SECONDS)
    return response

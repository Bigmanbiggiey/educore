import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def _clear_cache():
    # CACHES["default"] is Redis and backs DRF's throttle counters. Unlike
    # the DB, Redis isn't wrapped in each test's transaction rollback, so
    # anon-throttle hit counts accumulate across the whole pytest session —
    # a fast-running full suite can exhaust the 5/min anon bucket by the
    # time later test files run. Clear it before every test for isolation.
    cache.clear()
    yield

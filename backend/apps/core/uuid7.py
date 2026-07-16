"""RFC 9562 UUID version 7 generator.

Time-ordered UUIDs keep primary-key index locality under Postgres
(docs/database.md §1) without needing Python 3.14's built-in uuid.uuid7()
or an extra package — the algorithm is small enough to own directly, as
database.md anticipates ("via django-uuidv7 or a small custom default").

Uses a monotonic per-millisecond counter (RFC 9562 Method 1, §6.2) rather
than pure randomness for the 12 `rand_a` bits, so a burst of rows created
within the same millisecond — e.g. a CSV student-import request — still
sorts in generation order within this process. This is the actual case the
index-locality argument in database.md depends on; without it, "sorts
mostly-sequentially" would only be true across milliseconds, not within
one.
"""

import os
import threading
import time
import uuid

_COUNTER_BITS = 12
_COUNTER_MAX = (1 << _COUNTER_BITS) - 1

_lock = threading.Lock()
_last_ts_ms = 0
_last_counter = 0


def uuid7() -> uuid.UUID:
    global _last_ts_ms, _last_counter

    with _lock:
        ts_ms = int(time.time() * 1000)
        if ts_ms <= _last_ts_ms:
            ts_ms = _last_ts_ms
            _last_counter = (_last_counter + 1) & _COUNTER_MAX
            if _last_counter == 0:
                # Counter overflowed within the same millisecond — borrow
                # the next one rather than colliding.
                ts_ms += 1
        else:
            # New millisecond: reseed from the lower half of the counter
            # range (RFC 9562 §6.2) so the next increment can't collide
            # with a value an observer might have predicted.
            _last_counter = int.from_bytes(os.urandom(2), "big") & (_COUNTER_MAX >> 1)
        _last_ts_ms = ts_ms
        counter = _last_counter

    rand_b = int.from_bytes(os.urandom(8), "big") & 0x3FFFFFFFFFFFFFFF  # 62 random bits

    value = (
        (ts_ms & 0xFFFFFFFFFFFF) << 80
        | 0x7 << 76  # version
        | counter << 64
        | 0b10 << 62  # variant (RFC 4122)
        | rand_b
    )
    return uuid.UUID(int=value)

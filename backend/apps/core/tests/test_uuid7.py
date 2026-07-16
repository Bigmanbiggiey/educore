import uuid

from apps.core.uuid7 import uuid7


def test_uuid7_has_correct_version_and_variant():
    value = uuid7()
    assert value.version == 7
    assert value.variant == uuid.RFC_4122


def test_uuid7_values_are_unique():
    values = {uuid7() for _ in range(2000)}
    assert len(values) == 2000


def test_uuid7_sorts_in_generation_order():
    # The whole reason for choosing UUIDv7 over UUIDv4 (docs/database.md
    # §1) is Postgres B-tree insert locality for bulk-created rows within
    # the same millisecond — this is the guarantee that depends on.
    values = [uuid7() for _ in range(2000)]
    assert values == sorted(values)

"""Public write interface for `hostel` — docs/modules.md:
`services.allocate_bed(...)`. `create_hostel`/`create_room` are plain
wrappers — neither has an invariant beyond its own columns, same
"services.py is this app's complete public write API" shape `transport`/
`inventory` establish for their own plain-create models.

`allocate_bed` is the real one: it enforces the one invariant a bare
`BedAllocation.objects.create()` can't — a room's active-allocation count
for a given term must stay under `Room.capacity` — same "the service
enforces what a raw create can't" reasoning as `library.checkout`'s
availability check and `inventory.record_movement`'s stock check. A
duplicate student+term allocation is rejected by the DB constraint
(`bedallocation_one_per_student_per_term`) instead, surfaced here as the
same `ValueError` shape for a uniform caller experience.
"""

import uuid

from django.db import IntegrityError, transaction

from apps.core.context import bind_institution
from apps.hostel.models import BedAllocation, Hostel, Room
from apps.institutions.models import Institution


def create_hostel(*, institution: Institution, name: str) -> Hostel:
    with bind_institution(institution):
        return Hostel.objects.create(institution_id=institution.id, name=name)


def create_room(
    *, institution: Institution, hostel: Hostel, room_number: str, capacity: int
) -> Room:
    with bind_institution(institution):
        return Room.objects.create(
            institution_id=institution.id, hostel=hostel, room_number=room_number, capacity=capacity
        )


@transaction.atomic
def allocate_bed(
    *, institution: Institution, room: Room, student_id: uuid.UUID, term_id: uuid.UUID
) -> BedAllocation:
    with bind_institution(institution):
        occupied = BedAllocation.objects.filter(room=room, term_id=term_id).count()
        if occupied >= room.capacity:
            raise ValueError(
                f"Room {room} is at capacity for this term ({occupied}/{room.capacity})."
            )
        try:
            # A separate savepoint, not the outer atomic block itself: if
            # `.create()` hits the unique constraint below, only this
            # savepoint rolls back — catching the resulting IntegrityError
            # inside the *same* atomic block that raised it would otherwise
            # leave the whole transaction unusable for any further query.
            with transaction.atomic():
                return BedAllocation.objects.create(
                    institution_id=institution.id,
                    room=room,
                    student_id=student_id,
                    term_id=term_id,
                )
        except IntegrityError as exc:
            raise ValueError(
                f"Student {student_id} already has a bed allocation for this term."
            ) from exc

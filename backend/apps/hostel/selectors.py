"""Public read interface for `hostel` — docs/modules.md."""

import uuid

from apps.core.context import bind_institution
from apps.hostel.models import BedAllocation, Room
from apps.institutions.models import Institution


def get_occupancy(institution: Institution, room_id: uuid.UUID, term_id: uuid.UUID) -> dict:
    """The raw aggregate the "Occupancy Reports" deliverable needs — full
    reporting/export is Phase 8's `reports`/`analytics` job, not this app's."""
    with bind_institution(institution):
        room = Room.objects.get(pk=room_id)
        occupied = BedAllocation.objects.filter(room=room, term_id=term_id).count()
    return {"capacity": room.capacity, "occupied": occupied, "available": room.capacity - occupied}


def get_allocation_for_student(
    institution: Institution, student_id: uuid.UUID, term_id: uuid.UUID
) -> BedAllocation | None:
    with bind_institution(institution):
        return BedAllocation.objects.filter(student_id=student_id, term_id=term_id).first()

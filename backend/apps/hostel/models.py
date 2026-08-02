"""Layer 1 models — docs/database.md §3 ("Transport, Hostel"):

    Hostel → Room → BedAllocation (room, student, term)

`Room.hostel` is a real intra-app FK (`CASCADE`), same "→"-to-`CASCADE`
convention `Vehicle → Route` and `Timetable → Period` already established.
No separate `Bed` model: `BedAllocation`'s own field list is "(room,
student, term)", referencing `Room` directly, so individual bed slots are
counted via `Room.capacity` against the active-allocation count for a term,
not modeled as their own rows. `student_id`/`term_id` are plain cross-app
UUIDs to `students.Student`/`classes_streams.Term`, same convention as
every other cross-app reference in Layer 1 — `hostel` has no real Python
import of either. None of the three are on docs/database.md §1's
soft-delete list, so all three are plain `TenantScopedModel`.
"""

from django.db import models

from apps.core.models import TenantScopedModel


class Hostel(TenantScopedModel):
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Room(TenantScopedModel):
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name="rooms")
    room_number = models.CharField(max_length=50)
    capacity = models.PositiveIntegerField()

    class Meta:
        ordering = ["hostel", "room_number"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["hostel", "room_number"], name="room_unique_number_per_hostel"
        ),
    ]

    def __str__(self) -> str:
        return f"{self.hostel} — {self.room_number}"


class BedAllocation(TenantScopedModel):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="bed_allocations")
    student_id = models.UUIDField()
    term_id = models.UUIDField()

    class Meta:
        ordering = ["-created_at"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "student_id", "term_id"],
            name="bedallocation_one_per_student_per_term",
        ),
    ]

    def __str__(self) -> str:
        return f"{self.room} — student {self.student_id} — term {self.term_id}"

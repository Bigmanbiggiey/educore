"""Layer 1 models — docs/database.md §3 ("Attendance, Timetable"):

    Timetable (institution, term, class_grade)
      └─< Period (timetable, day_of_week, start_time, end_time)
            └─< SubjectSlotAssignment (period, subject, staff, room)
                  — clash-detection enforced in services.py, not just a DB
                    constraint, because "clash" spans multiple rows (same
                    staff, overlapping time).

`term`/`class_grade` (on `Timetable`) and `subject`/`staff` (on
`SubjectSlotAssignment`) are all cross-app references — to
`classes_streams.Term`/`ClassGrade`, `academics.SubjectCatalog`, and
`staff.StaffProfile` respectively — so they're plain `UUIDField`s, not real
FKs, per the sibling-app convention `classes_streams.models` documents.
`Period` and `SubjectSlotAssignment` reference their own app's parent via a
real FK, same as everywhere else intra-app relationships are modeled.

Neither model is on docs/database.md §1's soft-deletable list, so all three
are plain `TenantScopedModel`.
"""

from django.db import models

from apps.core.models import TenantScopedModel


class Timetable(TenantScopedModel):
    term_id = models.UUIDField()
    class_grade_id = models.UUIDField()

    class Meta:
        ordering = ["-created_at"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "term_id", "class_grade_id"],
            name="timetable_unique_per_term_class",
        ),
    ]

    def __str__(self) -> str:
        return f"Timetable — class {self.class_grade_id} — term {self.term_id}"


class Period(TenantScopedModel):
    class DayOfWeek(models.IntegerChoices):
        MONDAY = 0, "Monday"
        TUESDAY = 1, "Tuesday"
        WEDNESDAY = 2, "Wednesday"
        THURSDAY = 3, "Thursday"
        FRIDAY = 4, "Friday"
        SATURDAY = 5, "Saturday"
        SUNDAY = 6, "Sunday"

    timetable = models.ForeignKey(Timetable, on_delete=models.CASCADE, related_name="periods")
    day_of_week = models.IntegerField(choices=DayOfWeek.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ["day_of_week", "start_time"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["timetable", "day_of_week", "start_time"],
            name="period_unique_start_per_timetable_day",
        ),
        models.CheckConstraint(
            condition=models.Q(start_time__lt=models.F("end_time")),
            name="period_start_before_end",
        ),
    ]

    def __str__(self) -> str:
        return (
            f"{self.get_day_of_week_display()} {self.start_time}-{self.end_time} — {self.timetable}"
        )


class SubjectSlotAssignment(TenantScopedModel):
    period = models.ForeignKey(
        Period, on_delete=models.CASCADE, related_name="subject_slot_assignments"
    )
    subject_id = models.UUIDField()
    staff_id = models.UUIDField()
    room = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ["-created_at"]

    Meta.constraints = [
        # One assignment per period — `services.assign_slot` is the
        # sanctioned write path and already enforces this via
        # `update_or_create(period=...)`, but the constraint holds even
        # against direct ORM access that bypasses it.
        models.UniqueConstraint(fields=["period"], name="subjectslotassignment_one_per_period"),
    ]

    def __str__(self) -> str:
        return f"{self.period} — subject {self.subject_id} — staff {self.staff_id}"

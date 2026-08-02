"""Layer 1 models — docs/database.md §3 ("Transport, Hostel"):

    Vehicle → Route → Stop; TransportAssignment (student, route, stop)

`Route.vehicle` and `Stop.route` are real intra-app FKs (`CASCADE`), same
"→" -to-`CASCADE` convention `Timetable → Period` and `Book → Copy`
already established elsewhere in this codebase. `student_id` on
`TransportAssignment` is a plain cross-app UUID to `students.Student`, same
convention as every other cross-app reference in Layer 1 — `transport` has
no real Python import of `students`. None of the four are on
docs/database.md §1's soft-delete list, so all four are plain
`TenantScopedModel`.
"""

from django.db import models

from apps.core.models import TenantScopedModel


class Vehicle(TenantScopedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        UNDER_MAINTENANCE = "under_maintenance", "Under Maintenance"
        RETIRED = "retired", "Retired"

    registration_number = models.CharField(max_length=50)
    make_model = models.CharField(max_length=255, blank=True)
    capacity = models.PositiveIntegerField()
    driver_name = models.CharField(max_length=255, blank=True)
    driver_phone = models.CharField(max_length=30, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ["registration_number"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "registration_number"],
            name="vehicle_unique_registration_per_institution",
        ),
    ]

    def __str__(self) -> str:
        return self.registration_number


class Route(TenantScopedModel):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="routes")
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Stop(TenantScopedModel):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name="stops")
    name = models.CharField(max_length=255)
    sequence = models.PositiveIntegerField()

    class Meta:
        ordering = ["route", "sequence"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["route", "sequence"], name="stop_unique_sequence_per_route"
        ),
    ]

    def __str__(self) -> str:
        return f"{self.route} — #{self.sequence} {self.name}"


class TransportAssignment(TenantScopedModel):
    student_id = models.UUIDField()
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name="assignments")
    stop = models.ForeignKey(Stop, on_delete=models.CASCADE, related_name="assignments")

    class Meta:
        ordering = ["-created_at"]

    Meta.constraints = [
        # One active route/stop assignment per student —
        # `services.assign_transport` is `update_or_create`-keyed on this,
        # same idempotent-reassignment shape `clinic.set_health_record`
        # established.
        models.UniqueConstraint(
            fields=["institution_id", "student_id"],
            name="transportassignment_one_per_student",
        ),
    ]

    def __str__(self) -> str:
        return f"student {self.student_id} — {self.stop}"

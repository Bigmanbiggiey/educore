"""Layer 1 models — docs/database.md §3, docs/modules.md (`students`).

`Student`/`Enrollment` use `TenantScopedSoftDeleteModel` — both are named
explicitly in docs/database.md §1's soft-deletable list (a wrong
hard-delete of enrollment history is costly). `GuardianRelationship` isn't
on that list, so it's plain `TenantScopedModel` (hard-delete).

Cross-app references are plain UUIDFields, never real ForeignKeys:
`Student.user_id`/`GuardianRelationship.guardian_user_id` point at
`accounts.User`, which is platform-global and explicitly exempt from real
FKs from tenant-scoped models regardless of app (docs/database.md §1).
`Enrollment.class_grade_id`/`stream_id`/`term_id` point at `classes_streams`
models — a *sibling* Layer 1 app, not one of the two dependencies
`students` is allowed to import (docs/modules.md: only `parents` and
`admissions` import from `students`, never the reverse) — so these stay
plain UUIDs for the same reason every other cross-app reference does
(docs/multitenancy.md §1), not just the cross-database one.
"""

from django.db import models

from apps.core.models import TenantScopedModel, TenantScopedSoftDeleteModel


class Student(TenantScopedSoftDeleteModel):
    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"

    # Nullable: young students may have no login of their own
    # (docs/database.md §3). Plain UUID, not a real FK — accounts.User is
    # platform-global (see module docstring).
    user_id = models.UUIDField(null=True, blank=True)
    admission_number = models.CharField(max_length=50)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True, default="")

    class Meta:
        ordering = ["last_name", "first_name"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "admission_number"],
            name="student_unique_admission_number_per_institution",
        ),
    ]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} ({self.admission_number})"


class Enrollment(TenantScopedSoftDeleteModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        TRANSFERRED = "transferred", "Transferred"
        WITHDRAWN = "withdrawn", "Withdrawn"
        COMPLETED = "completed", "Completed"

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="enrollments")
    # Cross-app references to classes_streams — plain UUIDs (see module
    # docstring). stream_id nullable: a student may be enrolled in a class
    # grade before stream allocation happens.
    class_grade_id = models.UUIDField()
    stream_id = models.UUIDField(null=True, blank=True)
    term_id = models.UUIDField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ["-created_at"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["student", "term_id"], name="enrollment_unique_student_per_term"
        ),
        models.CheckConstraint(
            condition=models.Q(status__in=Status.values), name="enrollment_valid_status"
        ),
    ]

    def __str__(self) -> str:
        return f"{self.student} — {self.term_id} ({self.status})"


class GuardianRelationship(TenantScopedModel):
    """Lives here, not in `parents` — a guardian may have no `ParentProfile`/
    portal account at all (e.g. an emergency contact), so this relationship
    must not depend on that profile existing (docs/database.md §3)."""

    class RelationshipType(models.TextChoices):
        PARENT = "parent", "Parent"
        GUARDIAN = "guardian", "Guardian"
        EMERGENCY_CONTACT = "emergency_contact", "Emergency contact"
        OTHER = "other", "Other"

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="guardian_relationships"
    )
    # Cross-app reference to accounts.User — plain UUID (see module
    # docstring); always populated, unlike Student.user_id — a guardian
    # relationship only makes sense for a user who can actually log in.
    guardian_user_id = models.UUIDField()
    relationship_type = models.CharField(max_length=20, choices=RelationshipType.choices)
    is_primary_contact = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_primary_contact"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["student", "guardian_user_id"],
            name="guardianrelationship_unique_student_guardian",
        ),
    ]

    def __str__(self) -> str:
        return f"{self.guardian_user_id} — {self.get_relationship_type_display()} of {self.student}"

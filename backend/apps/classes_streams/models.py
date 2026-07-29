"""Layer 1 temporal-backbone models — docs/database.md §3, docs/modules.md
(`classes_streams`). "Build first" of the Phase 2 apps: nearly every other
Layer 1/2 table answers "as of when" by referencing `Term`, not a raw date
range, via `selectors.get_current_term(institution)`.

Intra-app references (`Term.academic_year`, `ClassGrade.term`, etc.) are
real Django ForeignKeys — the plain-`UUIDField` convention only applies to
*cross-app* references (docs/multitenancy.md §1: Django can't enforce FK
constraints across the database boundary a dedicated-DB tenant introduces,
so cross-app references stay plain UUIDs uniformly). `ClassTeacherAssignment.staff_id`
is a cross-app reference to `staff.StaffProfile` and is a plain UUIDField
for that reason.
"""

from django.db import models

from apps.core.models import TenantScopedModel
from apps.institutions.models import InstitutionCurriculum


class AcademicYear(TenantScopedModel):
    year_label = models.CharField(max_length=20)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        ordering = ["-start_date"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "year_label"],
            name="academicyear_unique_label_per_institution",
        ),
    ]

    def __str__(self) -> str:
        return self.year_label


class Term(TenantScopedModel):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name="terms")
    name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    # Administratively set (can be adjusted for e.g. a public holiday
    # extension), not derived from start_date/end_date — docs/database.md
    # §3's "temporal backbone" note: term boundaries aren't pure calendar
    # math, `get_current_term` is the one source of truth.
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ["-start_date"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["academic_year", "name"], name="term_unique_name_per_academic_year"
        ),
        # At most one current term per institution — uses this model's own
        # institution_id (every TenantScopedModel has one) rather than
        # traversing academic_year, so the constraint doesn't need a join.
        models.UniqueConstraint(
            fields=["institution_id"],
            condition=models.Q(is_current=True),
            name="term_one_current_per_institution",
        ),
    ]

    def __str__(self) -> str:
        return f"{self.academic_year} — {self.name}"


class ClassGrade(TenantScopedModel):
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name="class_grades")
    name = models.CharField(max_length=50)
    curriculum_type = models.CharField(
        max_length=20, choices=InstitutionCurriculum.CurriculumType.choices
    )

    class Meta:
        ordering = ["name"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["term", "name", "curriculum_type"], name="classgrade_unique_per_term"
        ),
        models.CheckConstraint(
            condition=models.Q(curriculum_type__in=InstitutionCurriculum.CurriculumType.values),
            name="classgrade_valid_curriculum_type",
        ),
    ]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_curriculum_type_display()}) — {self.term}"


class Stream(TenantScopedModel):
    class_grade = models.ForeignKey(ClassGrade, on_delete=models.CASCADE, related_name="streams")
    name = models.CharField(max_length=50)
    capacity = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["class_grade", "name"], name="stream_unique_name_per_class"
        ),
    ]

    def __str__(self) -> str:
        return f"{self.class_grade} {self.name}"


class ClassTeacherAssignment(TenantScopedModel):
    class_grade = models.ForeignKey(
        ClassGrade, on_delete=models.CASCADE, related_name="teacher_assignments"
    )
    # Nullable: some institutions assign a class teacher per ClassGrade as a
    # whole (no streams yet, or a single-stream grade); others assign per
    # Stream. The partial-unique constraints below enforce "at most one
    # active assignment" correctly for either shape.
    stream = models.ForeignKey(
        Stream, null=True, blank=True, on_delete=models.CASCADE, related_name="teacher_assignments"
    )
    term = models.ForeignKey(
        Term, on_delete=models.CASCADE, related_name="class_teacher_assignments"
    )
    # Cross-app reference to staff.StaffProfile — plain UUID, not a real FK
    # (see module docstring).
    staff_id = models.UUIDField()

    class Meta:
        ordering = ["-created_at"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["class_grade", "term"],
            condition=models.Q(stream__isnull=True),
            name="classteacher_unique_per_class_when_no_stream",
        ),
        models.UniqueConstraint(
            fields=["class_grade", "stream", "term"],
            condition=models.Q(stream__isnull=False),
            name="classteacher_unique_per_stream",
        ),
    ]

    def __str__(self) -> str:
        target = self.stream or self.class_grade
        return f"{target} class teacher — {self.term}"

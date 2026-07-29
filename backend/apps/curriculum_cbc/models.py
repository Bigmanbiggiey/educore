"""Layer 2 curriculum plugin — docs/database.md §4 (CBC), docs/modules.md's
Layer 2 table. Every table carries institution + a FK chain back to Student
and Term, same plain-cross-app-UUID convention as every Layer 1 app:
`subject_catalog_id`/`student_id`/`term_id` are `UUIDField`s, not real FKs,
to `academics.SubjectCatalog`/`students.Student`/`classes_streams.Term` —
docs/multitenancy.md §1's reasoning applies equally here, this is still a
`TenantScopedModel`. A real Django FK is used only for intra-app
relationships (`Competency.learning_area`, `Project.competency`,
`ContinuousAssessment.competency`).
"""

from django.db import models

from apps.core.models import TenantScopedModel


class LearningArea(TenantScopedModel):
    # Specializes academics.SubjectCatalog via FK, per docs/database.md §3's
    # "the generic subject concept curriculum plugins specialize via FK".
    subject_catalog_id = models.UUIDField()
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)

    class Meta:
        ordering = ["name"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "code"], name="learningarea_unique_code_per_institution"
        ),
    ]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class Competency(TenantScopedModel):
    learning_area = models.ForeignKey(
        LearningArea, on_delete=models.CASCADE, related_name="competencies"
    )
    strand = models.CharField(max_length=100)
    sub_strand = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["strand", "sub_strand"]

    def __str__(self) -> str:
        return f"{self.learning_area} — {self.strand}"


class CoreValue(TenantScopedModel):
    # Deliberately no seeded data — CBC's official core-value list is real
    # curriculum content, not something to guess/hardcode; institutions
    # enter their own.
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "name"], name="corevalue_unique_name_per_institution"
        ),
    ]

    def __str__(self) -> str:
        return self.name


class PCI(TenantScopedModel):
    """Pertinent & Contemporary Issue. Same "no seeded data" reasoning as
    `CoreValue`."""

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "PCI"
        verbose_name_plural = "PCIs"

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "name"], name="pci_unique_name_per_institution"
        ),
    ]

    def __str__(self) -> str:
        return self.name


class Project(TenantScopedModel):
    student_id = models.UUIDField()
    competency = models.ForeignKey(Competency, on_delete=models.CASCADE, related_name="projects")
    term_id = models.UUIDField()
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Project — student {self.student_id} — {self.competency}"


class ContinuousAssessment(TenantScopedModel):
    class PerformanceLevel(models.TextChoices):
        EXCEEDING_EXPECTATION = "exceeding_expectation", "Exceeding Expectation"
        MEETING_EXPECTATION = "meeting_expectation", "Meeting Expectation"
        APPROACHING_EXPECTATION = "approaching_expectation", "Approaching Expectation"
        BELOW_EXPECTATION = "below_expectation", "Below Expectation"

    student_id = models.UUIDField()
    competency = models.ForeignKey(
        Competency, on_delete=models.CASCADE, related_name="continuous_assessments"
    )
    term_id = models.UUIDField()
    performance_level = models.CharField(max_length=30, choices=PerformanceLevel.choices)
    evidence_notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "student_id", "competency", "term_id"],
            name="continuousassessment_unique_per_student_competency_term",
        ),
        models.CheckConstraint(
            condition=models.Q(performance_level__in=PerformanceLevel.values),
            name="continuousassessment_valid_performance_level",
        ),
    ]

    def __str__(self) -> str:
        return (
            f"{self.competency} — student {self.student_id} — "
            f"{self.get_performance_level_display()}"
        )

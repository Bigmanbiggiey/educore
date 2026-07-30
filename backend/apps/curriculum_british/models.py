"""Layer 2 curriculum plugin — docs/database.md §4 (British), docs/modules.md's
Layer 2 table. Same plain-cross-app-UUID convention as the other two
plugins.

"EYFSStage, KeyStage, YearGroup (curriculum-specific class-grade
equivalents, map to ClassGrade)" reads as one model (`YearGroup`), not
three tables — the docs give this trio one collective description, not a
field list per item, and Key Stages (EYFS, KS1-5) are a fixed, universally
standard structure, not institution-invented content — so `key_stage`
becomes a plain `TextChoices` field, the same "one model with a
discriminator" reading `curriculum_844`'s four exam types got.
"""

from django.db import models

from apps.core.models import TenantScopedModel


class YearGroup(TenantScopedModel):
    class KeyStage(models.TextChoices):
        EYFS = "eyfs", "EYFS"
        KS1 = "ks1", "Key Stage 1"
        KS2 = "ks2", "Key Stage 2"
        KS3 = "ks3", "Key Stage 3"
        KS4 = "ks4", "Key Stage 4"
        KS5 = "ks5", "Key Stage 5"

    # "Map to ClassGrade" per docs/database.md §4 — specializes it via a
    # plain cross-app UUID, same pattern as curriculum_cbc.LearningArea /
    # curriculum_844.Subject specializing academics.SubjectCatalog.
    class_grade_id = models.UUIDField()
    key_stage = models.CharField(max_length=10, choices=KeyStage.choices)
    name = models.CharField(max_length=50)
    order = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["order"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "class_grade_id"],
            name="yeargroup_unique_class_grade_per_institution",
        ),
        models.CheckConstraint(
            condition=models.Q(key_stage__in=KeyStage.values), name="yeargroup_valid_key_stage"
        ),
    ]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_key_stage_display()})"


class Subject(TenantScopedModel):
    class QualificationLevel(models.TextChoices):
        NONE = "none", "None"
        IGCSE = "igcse", "IGCSE"
        A_LEVEL = "a_level", "A-Level"

    subject_catalog_id = models.UUIDField()
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    qualification_level = models.CharField(
        max_length=10, choices=QualificationLevel.choices, default=QualificationLevel.NONE
    )

    class Meta:
        ordering = ["name"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "code"], name="subjectbritish_unique_code_per_institution"
        ),
    ]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class Coursework(TenantScopedModel):
    # score/max_score aren't in docs/database.md §4's literal field list for
    # Coursework (only "score" is named) — added as a deliberate, minimal
    # completion: a raw score with no denominator can't be aggregated into
    # a mean/grade, which this plugin needs to do.
    student_id = models.UUIDField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="courseworks")
    term_id = models.UUIDField()
    component = models.CharField(max_length=100)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    max_score = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        ordering = ["-created_at"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "student_id", "subject", "term_id", "component"],
            name="coursework_unique_per_student_subject_term_component",
        ),
        models.CheckConstraint(
            condition=models.Q(score__gte=0), name="coursework_score_non_negative"
        ),
        models.CheckConstraint(
            condition=models.Q(max_score__gt=0), name="coursework_max_score_positive"
        ),
        models.CheckConstraint(
            condition=models.Q(score__lte=models.F("max_score")), name="coursework_score_within_max"
        ),
    ]

    def __str__(self) -> str:
        return f"{self.subject} — student {self.student_id} — {self.component}"


class PredictedGrade(TenantScopedModel):
    """A teacher's standing judgment for UCAS/university applications — set
    directly, not derived from `Coursework`. Scoped to `academic_year`, not
    `term` (docs/database.md §4), unlike every other assessment model in
    this project so far."""

    student_id = models.UUIDField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="predicted_grades")
    academic_year_id = models.UUIDField()
    predicted_grade = models.CharField(max_length=10)
    # Cross-app reference to accounts.User — injected server-side from
    # request.user.id, never client-supplied, same "server sets
    # audit-relevant fields" convention used for institution_id everywhere.
    set_by = models.UUIDField()

    class Meta:
        ordering = ["-updated_at"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "student_id", "subject", "academic_year_id"],
            name="predictedgrade_unique_per_student_subject_year",
        ),
    ]

    def __str__(self) -> str:
        return f"{self.subject} — student {self.student_id} — {self.predicted_grade}"

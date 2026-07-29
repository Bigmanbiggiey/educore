"""Layer 2 curriculum plugin — docs/database.md §4 (8-4-4), docs/modules.md's
Layer 2 table. Same plain-cross-app-UUID convention as `curriculum_cbc`:
`subject_catalog_id`/`student_id`/`term_id` are `UUIDField`s, not real FKs.
"CAT, Midterm, EndTerm, Mock (student, subject, term, score, max_score,
exam_type)" reads as one model with an `exam_type` discriminator, not four
near-identical tables — `exam_type` is listed as a shared field alongside
the rest, not four separate parenthetical groups.
"""

from django.db import models

from apps.core.models import TenantScopedModel


class Subject(TenantScopedModel):
    # Specializes academics.SubjectCatalog via FK, same pattern as
    # curriculum_cbc.LearningArea (docs/database.md §3).
    subject_catalog_id = models.UUIDField()
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)

    class Meta:
        ordering = ["name"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "code"], name="subject844_unique_code_per_institution"
        ),
    ]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class ExamResult(TenantScopedModel):
    class ExamType(models.TextChoices):
        CAT = "cat", "CAT"
        MIDTERM = "midterm", "Midterm"
        END_TERM = "end_term", "End Term"
        MOCK = "mock", "Mock"
        KCPE_KCSE = "kcpe_kcse", "KCPE/KCSE"

    student_id = models.UUIDField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="exam_results")
    term_id = models.UUIDField()
    exam_type = models.CharField(max_length=20, choices=ExamType.choices)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    max_score = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        ordering = ["-created_at"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "student_id", "subject", "term_id", "exam_type"],
            name="examresult_unique_per_student_subject_term_type",
        ),
        models.CheckConstraint(
            condition=models.Q(score__gte=0), name="examresult_score_non_negative"
        ),
        models.CheckConstraint(
            condition=models.Q(max_score__gt=0), name="examresult_max_score_positive"
        ),
        models.CheckConstraint(
            condition=models.Q(score__lte=models.F("max_score")), name="examresult_score_within_max"
        ),
        models.CheckConstraint(
            condition=models.Q(exam_type__in=ExamType.values), name="examresult_valid_exam_type"
        ),
    ]

    def __str__(self) -> str:
        return (
            f"{self.subject} — student {self.student_id} — "
            f"{self.get_exam_type_display()}: {self.score}/{self.max_score}"
        )


class MeanGradeSnapshot(TenantScopedModel):
    """Precomputed, not request-time — docs/database.md §4: ranking needs
    every student in the class recomputed together, so this is only ever
    written by `services.recompute_mean_grade_snapshots` (via the Celery
    task in `tasks.py`), never live per request."""

    student_id = models.UUIDField()
    term_id = models.UUIDField()
    mean_score = models.DecimalField(max_digits=5, decimal_places=2)
    mean_grade = models.CharField(max_length=10)
    rank_in_class = models.PositiveIntegerField(null=True, blank=True)
    rank_in_stream = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-updated_at"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "student_id", "term_id"],
            name="meangradesnapshot_unique_per_student_term",
        ),
    ]

    def __str__(self) -> str:
        return f"Mean grade — student {self.student_id} — {self.term_id}: {self.mean_grade}"

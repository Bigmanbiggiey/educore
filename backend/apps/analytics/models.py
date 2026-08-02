"""Layer 3 models — docs/modules.md (`analytics`): "Celery-driven rollups
(attendance rates, fee collection %, mean grade trends) — precomputed, not
calculated on every dashboard request."

All three rollups share one shape — `(institution, class_grade, term)` —
for consistency, and are all plain `TenantScopedModel` (none is on
docs/database.md §1's soft-delete list; these are derived/recomputable
data, not records of anything that happened). `class_grade_id`/`term_id`
are plain cross-app UUIDs to `classes_streams.ClassGrade`/`Term`, same
convention as every other cross-app reference in this codebase — `analytics`
has no real Python import of `classes_streams`'s *models*, only its
selectors (see `services.py`).

`services.compute_rollups` is `update_or_create`-keyed on each model's
unique constraint, same idempotent-recompute shape
`curriculum_844.services.recompute_mean_grade_snapshots` established for
its own precomputed `MeanGradeSnapshot`.
"""

from django.db import models

from apps.core.models import TenantScopedModel


class AttendanceRateSnapshot(TenantScopedModel):
    class_grade_id = models.UUIDField()
    term_id = models.UUIDField()
    # Nullable — `None` means no attendance records exist yet for this
    # class/term, not a 0% rate. Same convention `attendance.selectors.
    # get_attendance_rate` established for exactly this reason.
    rate = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)

    class Meta:
        ordering = ["-updated_at"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "class_grade_id", "term_id"],
            name="attendanceratesnapshot_unique_per_class_term",
        ),
    ]

    def __str__(self) -> str:
        return f"Attendance rollup — class {self.class_grade_id} — {self.term_id}: {self.rate}"


class FeeCollectionSnapshot(TenantScopedModel):
    class_grade_id = models.UUIDField()
    term_id = models.UUIDField()
    total_due = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_collected = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    # Nullable — `None` when `total_due` is 0 (nothing invoiced yet), not a
    # divide-by-zero forced to 0 or 100.
    collection_rate = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)

    class Meta:
        ordering = ["-updated_at"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "class_grade_id", "term_id"],
            name="feecollectionsnapshot_unique_per_class_term",
        ),
    ]

    def __str__(self) -> str:
        return f"Fee rollup — class {self.class_grade_id} — {self.term_id}: {self.collection_rate}"


class MeanGradeRollup(TenantScopedModel):
    class_grade_id = models.UUIDField()
    term_id = models.UUIDField()
    # Both nullable — populated only for classes running curriculum `844`
    # (the only plugin with a numeric mean-grade concept; CBC's 4-tier
    # performance levels have no mean-score equivalent). `None` for every
    # other curriculum, not a guessed number — docs/checklist.md's own
    # "don't build what nothing backs yet" discipline.
    mean_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    mean_grade = models.CharField(max_length=10, blank=True)

    class Meta:
        ordering = ["-updated_at"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "class_grade_id", "term_id"],
            name="meangraderollup_unique_per_class_term",
        ),
    ]

    def __str__(self) -> str:
        return (
            f"Mean grade rollup — class {self.class_grade_id} — {self.term_id}: {self.mean_grade}"
        )

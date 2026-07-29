"""Layer 1 models — docs/database.md §3:

    Application (institution, applicant_details[JSONB or child table], stage,
                 term_applying_for)
      └─< Offer (application, offered_at, accepted_at) → on accept: Enrollment created

`ApplicationStage` (named separately in docs/modules.md) is the append-only
history of stage transitions — `Application.stage` stays the fast-to-filter
current value, `ApplicationStage` rows are the timestamped audit trail of
how it got there, same "current value + history table" split `audit.AuditLog`
already established project-wide.

`term_applying_for_id` is a plain cross-app UUID to `classes_streams.Term`,
same convention as every other cross-app reference in Layer 1. None of
these are on docs/database.md §1's soft-delete list, so all three are plain
`TenantScopedModel`.
"""

from django.db import models

from apps.core.models import TenantScopedModel


class Application(TenantScopedModel):
    class Stage(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        UNDER_REVIEW = "under_review", "Under Review"
        OFFERED = "offered", "Offered"
        ACCEPTED = "accepted", "Accepted"
        ENROLLED = "enrolled", "Enrolled"
        REJECTED = "rejected", "Rejected"
        WITHDRAWN = "withdrawn", "Withdrawn"

    # Deliberately unstructured — applicant name/DOB/guardian contact/etc
    # vary too much across institutions to justify a fixed schema, same
    # reasoning as `academics.GradingScale.levels`.
    applicant_details = models.JSONField(default=dict, blank=True)
    stage = models.CharField(max_length=20, choices=Stage.choices, default=Stage.SUBMITTED)
    term_applying_for_id = models.UUIDField()

    class Meta:
        ordering = ["-created_at"]

    Meta.constraints = [
        models.CheckConstraint(
            condition=models.Q(stage__in=Stage.values), name="application_valid_stage"
        ),
    ]

    def __str__(self) -> str:
        return f"Application {self.id} — {self.get_stage_display()}"


class ApplicationStage(TenantScopedModel):
    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="stage_history"
    )
    stage = models.CharField(max_length=20, choices=Application.Stage.choices)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.application_id} — {self.get_stage_display()}"


class Offer(TenantScopedModel):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="offers")
    offered_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-offered_at"]

    def __str__(self) -> str:
        return f"Offer — {self.application_id} — offered {self.offered_at}"

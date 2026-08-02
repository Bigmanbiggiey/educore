"""Layer 1 models — docs/database.md §3 ("Library, Inventory, Transport,
Hostel, Clinic"):

    HealthRecord (student, allergies, conditions) → ClinicVisit (student,
                                                                   date, notes, treated_by)

`Medication` is named separately in docs/modules.md's own entity list for
this app (`HealthRecord`, `ClinicVisit`, `Medication`) as medication
administered during a specific visit, so it's modeled as a real intra-app
FK to `ClinicVisit` rather than its own student reference. `student_id`/
`treated_by_id` are plain cross-app UUIDs to `students.Student`/
`staff.StaffProfile`, same convention as every other cross-app reference in
Layer 1 — `clinic` has no real Python import of either sibling app. None of
the three are on docs/database.md §1's soft-delete list, so all three are
plain `TenantScopedModel`.

docs/modules.md calls this app's selectors out specifically as
"access-restricted (nurse role only — enforced via permissions)" — medical
data is sensitive enough that even *reads* need a permission check, unlike
every other Layer 1 app's "any active member may read" default. That
restriction lives in `views.py` (permission classes gate the request, same
as every other app's writes), not here or in `selectors.py` — a selector
has no `request` to check a permission against, and the RBAC/object-scope
split docs/permissions.md §3 draws puts this squarely in the RBAC layer.
"""

from django.db import models

from apps.core.models import TenantScopedModel


class HealthRecord(TenantScopedModel):
    student_id = models.UUIDField()
    allergies = models.TextField(blank=True)
    conditions = models.TextField(blank=True)
    blood_group = models.CharField(max_length=10, blank=True)

    class Meta:
        ordering = ["-created_at"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "student_id"], name="healthrecord_one_per_student"
        ),
    ]

    def __str__(self) -> str:
        return f"Health record — student {self.student_id}"


class ClinicVisit(TenantScopedModel):
    student_id = models.UUIDField()
    visit_date = models.DateField()
    treated_by_id = models.UUIDField()
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-visit_date"]

    def __str__(self) -> str:
        return f"Visit — student {self.student_id} — {self.visit_date}"


class Medication(TenantScopedModel):
    visit = models.ForeignKey(ClinicVisit, on_delete=models.CASCADE, related_name="medications")
    name = models.CharField(max_length=255)
    dosage = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} — {self.visit}"

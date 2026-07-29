"""Layer 1 shared tables `academics` owns directly — docs/database.md §3.
Not the curriculum contract itself (see `contracts.py`), but the generic
concepts curriculum plugins specialize via FK rather than each curriculum
app inventing its own: "the generic 'subject' concept curriculum plugins
specialize via FK, e.g. `curriculum_844.CAT` references `SubjectCatalog`,
not a separate subject list per curriculum plugin."

Neither model is on docs/database.md §1's soft-deletable list, so both are
plain `TenantScopedModel`.
"""

from django.db import models

from apps.core.models import TenantScopedModel
from apps.institutions.models import InstitutionCurriculum


class GradingScale(TenantScopedModel):
    curriculum_type = models.CharField(
        max_length=20, choices=InstitutionCurriculum.CurriculumType.choices
    )
    # e.g. [{"label": "Exceeding Expectation", "min": 80, "max": 100}, ...]
    # — curriculum-specific level definitions, deliberately not normalized
    # into their own table: this is exactly the "levels[JSONB]" shape
    # docs/database.md §3 fixes for this model.
    levels = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["curriculum_type"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "curriculum_type"],
            name="gradingscale_unique_per_institution_curriculum",
        ),
        models.CheckConstraint(
            condition=models.Q(curriculum_type__in=InstitutionCurriculum.CurriculumType.values),
            name="gradingscale_valid_curriculum_type",
        ),
    ]

    def __str__(self) -> str:
        return f"Grading scale — {self.get_curriculum_type_display()}"


class SubjectCatalog(TenantScopedModel):
    curriculum_type = models.CharField(
        max_length=20, choices=InstitutionCurriculum.CurriculumType.choices
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)

    class Meta:
        ordering = ["name"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "curriculum_type", "code"],
            name="subjectcatalog_unique_code_per_institution_curriculum",
        ),
        models.CheckConstraint(
            condition=models.Q(curriculum_type__in=InstitutionCurriculum.CurriculumType.values),
            name="subjectcatalog_valid_curriculum_type",
        ),
    ]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

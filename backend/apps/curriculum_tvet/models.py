"""Layer 2 curriculum plugin — docs/database.md §4 (TVET), docs/modules.md's
Layer 2 table. Same plain-cross-app-UUID convention as the other three
plugins.

The most hierarchical plugin so far (Department -> Course -> CompetencyUnit)
and the first whose top-level entity (`Course`) is NOT documented as
specializing `academics.SubjectCatalog` — every other plugin's equivalent
did. Respecting that absence rather than forcing the pattern: vocational
courses aren't "subjects" in the school sense.

"WorkshopAssessment, PracticalExam (student, competency_unit, term, score,
assessor)" reads as one model (`PracticalAssessment`) with an
`assessment_type` discriminator — the same "shared field list, no
per-item breakdown" reading that collapsed 8-4-4's four exam types and
British's EYFS/KeyStage/YearGroup trio.
"""

from django.db import models
from django.utils import timezone

from apps.core.models import TenantScopedModel


class TVETDepartment(TenantScopedModel):
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["name"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "name"], name="tvetdepartment_unique_name_per_institution"
        ),
    ]

    def __str__(self) -> str:
        return self.name


class Course(TenantScopedModel):
    department = models.ForeignKey(TVETDepartment, on_delete=models.CASCADE, related_name="courses")
    course_code = models.CharField(max_length=20)
    # Not in docs/database.md §4's literal field list — added for the same
    # "can't display/manage a row with no name" reason CompetencyUnit's
    # name is added below.
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["name"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "course_code"], name="course_unique_code_per_institution"
        ),
    ]

    def __str__(self) -> str:
        return f"{self.name} ({self.course_code})"


class CompetencyUnit(TenantScopedModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="competency_units")
    unit_code = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    credit_hours = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["unit_code"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "course", "unit_code"],
            name="competencyunit_unique_code_per_course",
        ),
    ]

    def __str__(self) -> str:
        return f"{self.name} ({self.unit_code})"


class IndustrialAttachment(TenantScopedModel):
    """A placement record, not an assessment — no `AssessmentEngine`/
    `ReportEngine` role, but still surfaced in `generate_report_data`, same
    "own CRUD, appears in the report" precedent as `curriculum_cbc.Project`.
    """

    student_id = models.UUIDField()
    host_organization = models.CharField(max_length=150)
    start_date = models.DateField()
    end_date = models.DateField()
    supervisor_report = models.TextField(blank=True)

    class Meta:
        ordering = ["-start_date"]

    Meta.constraints = [
        models.CheckConstraint(
            condition=models.Q(start_date__lt=models.F("end_date")),
            name="industrialattachment_start_before_end",
        ),
    ]

    def __str__(self) -> str:
        return f"student {self.student_id} — {self.host_organization}"


class PracticalAssessment(TenantScopedModel):
    class AssessmentType(models.TextChoices):
        WORKSHOP = "workshop", "Workshop Assessment"
        PRACTICAL_EXAM = "practical_exam", "Practical Exam"

    student_id = models.UUIDField()
    competency_unit = models.ForeignKey(
        CompetencyUnit, on_delete=models.CASCADE, related_name="practical_assessments"
    )
    term_id = models.UUIDField()
    assessment_type = models.CharField(max_length=20, choices=AssessmentType.choices)
    # score/max_score aren't both in docs/database.md §4's literal field
    # list (only "score" is named) — max_score added as a deliberate,
    # minimal completion: a raw score with no denominator can't be
    # aggregated into a mean/grade, same reasoning as
    # curriculum_british.Coursework.
    score = models.DecimalField(max_digits=5, decimal_places=2)
    max_score = models.DecimalField(max_digits=5, decimal_places=2)
    # The staff member who graded this — plain cross-app UUID to
    # staff.StaffProfile, not validated for existence (same convention as
    # every other cross-app reference in Layer 1/2).
    assessor_id = models.UUIDField()

    class Meta:
        ordering = ["-created_at"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=[
                "institution_id",
                "student_id",
                "competency_unit",
                "term_id",
                "assessment_type",
            ],
            name="practicalassessment_unique_per_student_unit_term_type",
        ),
        models.CheckConstraint(
            condition=models.Q(score__gte=0), name="practicalassessment_score_non_negative"
        ),
        models.CheckConstraint(
            condition=models.Q(max_score__gt=0), name="practicalassessment_max_score_positive"
        ),
        models.CheckConstraint(
            condition=models.Q(score__lte=models.F("max_score")),
            name="practicalassessment_score_within_max",
        ),
    ]

    def __str__(self) -> str:
        return (
            f"{self.competency_unit} — student {self.student_id} — "
            f"{self.get_assessment_type_display()}"
        )


class Certificate(TenantScopedModel):
    """A staff-issued completion record — no automated completion-eligibility
    check invented, since nothing in the docs specifies one."""

    student_id = models.UUIDField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="certificates")
    issued_at = models.DateTimeField(default=timezone.now)
    certificate_number = models.CharField(max_length=50)

    class Meta:
        ordering = ["-issued_at"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "certificate_number"],
            name="certificate_unique_number_per_institution",
        ),
    ]

    def __str__(self) -> str:
        return f"{self.certificate_number} — student {self.student_id} — {self.course}"

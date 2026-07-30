"""Layer 2 curriculum plugin — docs/database.md §4 (University), docs/modules.md's
Layer 2 table. Same plain-cross-app-UUID convention as the other four
plugins for cross-app references; real intra-app FKs for everything that
lives in this app.

"Faculty -> School -> Department -> Programme" uses arrows, not commas —
a real hierarchy of genuinely distinct entities (matches how
Timetable -> Period -> SubjectSlotAssignment was built as three separate
models in Phase 2, not merged). These stay four separate models, unlike
the comma-separated "shared field list" groups every other plugin
collapsed into one model with a discriminator (8-4-4's four exam types,
British's EYFS/KeyStage/YearGroup, TVET's two assessment types).
"Assignment, CAT, FinalExam (student, unit, semester, score, max_score)"
is back to that shape, so it collapses to one `UnitAssessment` model.

`Department` is named `UniversityDepartment` here specifically to avoid
the cross-plugin `SubjectSerializer` naming collision
`curriculum_844`/`curriculum_british` hit (caught by
`spectacular --fail-on-warn`) — `curriculum_tvet` already owns
`TVETDepartment`.
"""

from django.db import models

from apps.core.models import TenantScopedModel


class Faculty(TenantScopedModel):
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["name"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "name"], name="faculty_unique_name_per_institution"
        ),
    ]

    def __str__(self) -> str:
        return self.name


class School(TenantScopedModel):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name="schools")
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["name"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "faculty", "name"], name="school_unique_name_per_faculty"
        ),
    ]

    def __str__(self) -> str:
        return f"{self.name} ({self.faculty})"


class UniversityDepartment(TenantScopedModel):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="departments")
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["name"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "school", "name"],
            name="universitydepartment_unique_name_per_school",
        ),
    ]

    def __str__(self) -> str:
        return f"{self.name} ({self.school})"


class Programme(TenantScopedModel):
    class DegreeLevel(models.TextChoices):
        CERTIFICATE = "certificate", "Certificate"
        DIPLOMA = "diploma", "Diploma"
        BACHELORS = "bachelors", "Bachelor's"
        MASTERS = "masters", "Master's"
        PHD = "phd", "PhD"

    department = models.ForeignKey(
        UniversityDepartment, on_delete=models.CASCADE, related_name="programmes"
    )
    programme_code = models.CharField(max_length=20)
    degree_level = models.CharField(max_length=20, choices=DegreeLevel.choices)
    name = models.CharField(max_length=150)

    class Meta:
        ordering = ["name"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "programme_code"],
            name="programme_unique_code_per_institution",
        ),
    ]

    def __str__(self) -> str:
        return f"{self.name} ({self.programme_code})"


class Unit(TenantScopedModel):
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name="units")
    unit_code = models.CharField(max_length=20)
    # Not in docs/database.md §4's literal field list — same
    # "can't display/manage a row with no name" addition every other
    # plugin's unit-like model got. No subject_catalog_id — units aren't
    # "subjects" in the school sense, same call as curriculum_tvet.Course.
    name = models.CharField(max_length=100)
    credit_hours = models.PositiveSmallIntegerField()
    # Which semester NUMBER a unit is typically offered in (e.g. 1 or 2) —
    # distinct from the Semester model below, which is a specific
    # term-instance, not a generic slot number.
    semester_offered = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["unit_code"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "unit_code"], name="unit_unique_code_per_institution"
        ),
    ]

    def __str__(self) -> str:
        return f"{self.name} ({self.unit_code})"


class Semester(TenantScopedModel):
    """Specializes `classes_streams.Term` for university calendars, same
    "map to X via a plain UUID" pattern as `curriculum_british.YearGroup`
    mapping to `ClassGrade` — not a parallel temporal system."""

    term_id = models.UUIDField()
    number = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=50)

    class Meta:
        ordering = ["-created_at"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "term_id"], name="semester_unique_term_per_institution"
        ),
    ]

    def __str__(self) -> str:
        return self.name


class CourseRegistration(TenantScopedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        DROPPED = "dropped", "Dropped"

    student_id = models.UUIDField()
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="registrations")
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name="registrations")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ["-created_at"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "student_id", "unit", "semester"],
            name="courseregistration_unique_per_student_unit_semester",
        ),
    ]

    def __str__(self) -> str:
        return f"student {self.student_id} — {self.unit} — {self.semester}"


class UnitAssessment(TenantScopedModel):
    class AssessmentType(models.TextChoices):
        ASSIGNMENT = "assignment", "Assignment"
        CAT = "cat", "CAT"
        FINAL_EXAM = "final_exam", "Final Exam"

    student_id = models.UUIDField()
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="assessments")
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name="assessments")
    assessment_type = models.CharField(max_length=20, choices=AssessmentType.choices)
    # score/max_score both DecimalFields, not float — precision matters at
    # grade boundaries, same convention every other plugin's assessment
    # model uses.
    score = models.DecimalField(max_digits=5, decimal_places=2)
    max_score = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        ordering = ["-created_at"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "student_id", "unit", "semester", "assessment_type"],
            name="unitassessment_unique_per_student_unit_semester_type",
        ),
        models.CheckConstraint(
            condition=models.Q(score__gte=0), name="unitassessment_score_non_negative"
        ),
        models.CheckConstraint(
            condition=models.Q(max_score__gt=0), name="unitassessment_max_score_positive"
        ),
        models.CheckConstraint(
            condition=models.Q(score__lte=models.F("max_score")),
            name="unitassessment_score_within_max",
        ),
    ]

    def __str__(self) -> str:
        return f"{self.unit} — student {self.student_id} — {self.get_assessment_type_display()}"


class GPASnapshot(TenantScopedModel):
    """Precomputed, not request-time — "same rationale as MeanGradeSnapshot"
    (docs/database.md §4): GPA/CGPA need every unit a student took in (or
    up to) a semester recomputed together, so this is only ever written by
    `services.recompute_gpa_snapshots` (via the Celery task in
    `tasks.py`), never live per request."""

    student_id = models.UUIDField()
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name="gpa_snapshots")
    gpa = models.DecimalField(max_digits=4, decimal_places=2)
    cgpa = models.DecimalField(max_digits=4, decimal_places=2)

    class Meta:
        ordering = ["-updated_at"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "student_id", "semester"],
            name="gpasnapshot_unique_per_student_semester",
        ),
    ]

    def __str__(self) -> str:
        return f"GPA — student {self.student_id} — {self.semester}: {self.gpa}"


class Dissertation(TenantScopedModel):
    class Status(models.TextChoices):
        PROPOSED = "proposed", "Proposed"
        IN_PROGRESS = "in_progress", "In Progress"
        SUBMITTED = "submitted", "Submitted"
        APPROVED = "approved", "Approved"

    student_id = models.UUIDField()
    # Cross-app reference to staff.StaffProfile — plain UUID, not validated
    # for existence, same convention as every other cross-app reference.
    supervisor_id = models.UUIDField()
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PROPOSED)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.title} — student {self.student_id}"


class Graduation(TenantScopedModel):
    student_id = models.UUIDField()
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name="graduations")
    conferred_at = models.DateTimeField()
    # Plain CharField, not an enum — degree classification conventions vary
    # too much by institution/country to hardcode a fixed set, same
    # reasoning that kept CBC's Core Values/PCIs institution-editable.
    classification = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["-conferred_at"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "student_id", "programme"],
            name="graduation_unique_per_student_programme",
        ),
    ]

    def __str__(self) -> str:
        return f"student {self.student_id} — {self.programme}"

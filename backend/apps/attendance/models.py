"""Layer 1 model — docs/database.md §3 ("Attendance, Timetable"):

    AttendanceRecord (institution, term, date, subject_type[student|staff],
                       target_id, status[present|absent|late|excused])
      — unique_together (term, date, subject_type, target_id)

`target_id` is a plain cross-app UUID — `students.Student` when
`subject_type=STUDENT`, `staff.StaffProfile` when `subject_type=STAFF` —
same reasoning as every other cross-app reference in Layer 1: no real FK
across the sibling-app boundary. Not on docs/database.md §1's soft-delete
list, so this is a plain `TenantScopedModel`.
"""

from django.db import models

from apps.core.models import TenantScopedModel


class AttendanceRecord(TenantScopedModel):
    class SubjectType(models.TextChoices):
        STUDENT = "student", "Student"
        STAFF = "staff", "Staff"

    class Status(models.TextChoices):
        PRESENT = "present", "Present"
        ABSENT = "absent", "Absent"
        LATE = "late", "Late"
        EXCUSED = "excused", "Excused"

    term_id = models.UUIDField()
    date = models.DateField()
    subject_type = models.CharField(max_length=10, choices=SubjectType.choices)
    target_id = models.UUIDField()
    status = models.CharField(max_length=10, choices=Status.choices)

    class Meta:
        ordering = ["-date"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "term_id", "date", "subject_type", "target_id"],
            name="attendancerecord_unique_per_term_date_target",
        ),
    ]

    def __str__(self) -> str:
        return (
            f"{self.get_subject_type_display()} {self.target_id} — "
            f"{self.date} — {self.get_status_display()}"
        )

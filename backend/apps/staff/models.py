"""Layer 1 model — docs/database.md §3, docs/modules.md (`staff`).
`StaffProfile` is named in docs/database.md §1's soft-deletable list
("Staff"), so it uses `TenantScopedSoftDeleteModel`.

`user_id` is a plain UUIDField, not a real FK — `accounts.User` is
platform-global and exempt from real FKs from any tenant-scoped model
(docs/database.md §1) — and, unlike `Student.user`, it's required: every
staff member has a platform login (docs/database.md §3 lists it as
`user[1:1]`, without `Student.user`'s explicit "[nullable]").

`first_name`/`last_name` aren't in docs/database.md §3's StaffProfile field
list, but `accounts.User` is identity-only (email/phone/password, no name
fields — docs/database.md §2) and that list is documented as "distinctive"
fields, not exhaustive — a staff member needs a displayable name from
somewhere, so this mirrors `students.Student`'s own name fields, the one
other model with the same gap.
"""

from django.db import models

from apps.core.models import TenantScopedSoftDeleteModel


class StaffProfile(TenantScopedSoftDeleteModel):
    class EmploymentType(models.TextChoices):
        FULL_TIME = "full_time", "Full-time"
        PART_TIME = "part_time", "Part-time"
        CONTRACT = "contract", "Contract"

    user_id = models.UUIDField()
    employee_number = models.CharField(max_length=50)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    department = models.CharField(max_length=100, blank=True, default="")
    employment_type = models.CharField(max_length=20, choices=EmploymentType.choices)
    hire_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "employee_number"],
            name="staffprofile_unique_employee_number_per_institution",
        ),
        models.UniqueConstraint(
            fields=["institution_id", "user_id"],
            name="staffprofile_unique_user_per_institution",
        ),
    ]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} ({self.employee_number})"

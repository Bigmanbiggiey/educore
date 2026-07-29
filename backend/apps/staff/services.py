"""Public write interface for `staff` — docs/modules.md. Other apps mutate
this app's state only through these functions, never by touching
apps.staff.models directly (docs/project-structure.md §3).

Binds `institution` for the duration of every write, exactly like
`classes_streams.services`/`students.services` — see either module's
docstring for why.
"""

import datetime
import uuid

from apps.core.context import bind_institution
from apps.institutions.models import Institution
from apps.staff.models import StaffProfile


def create_staff_profile(
    *,
    institution: Institution,
    user_id: uuid.UUID,
    employee_number: str,
    first_name: str,
    last_name: str,
    employment_type: str,
    department: str = "",
    hire_date: datetime.date | None = None,
) -> StaffProfile:
    if employment_type not in StaffProfile.EmploymentType.values:
        raise ValueError(f"Unknown employment type: {employment_type!r}")
    with bind_institution(institution):
        return StaffProfile.objects.create(
            institution_id=institution.id,
            user_id=user_id,
            employee_number=employee_number,
            first_name=first_name,
            last_name=last_name,
            department=department,
            employment_type=employment_type,
            hire_date=hire_date,
        )

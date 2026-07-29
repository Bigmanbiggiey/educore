"""Public read interface for `staff` — docs/modules.md.

docs/modules.md's `get_teachers_for_subject(...)` and docs/permissions.md
§3's `get_assigned_classes(staff_user)` (the Teacher-role object-scope
selector) are deliberately **not** built here yet: both need data this app
doesn't own and has no sanctioned import of — subject specialization lives
in `academics.SubjectCatalog` (not built until later this phase) and actual
class/subject assignments live in `timetable.SubjectSlotAssignment` (built
after `staff`, per docs/checklist.md's fixed order). Building either now
would mean guessing at a shape neither dependency has fixed yet. Add them
once `academics`/`timetable` exist to call into.
"""

import uuid

from apps.staff.models import StaffProfile


def get_staff_by_user_id(user_id: uuid.UUID) -> StaffProfile | None:
    return StaffProfile.objects.filter(user_id=user_id).first()


def get_staff_by_department(department: str):
    return StaffProfile.objects.filter(department=department)

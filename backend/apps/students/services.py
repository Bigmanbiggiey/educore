"""Public write interface for `students` — docs/modules.md. Other apps
mutate this app's state only through these functions, never by touching
apps.students.models directly (docs/project-structure.md §3).
`enroll_student` is the one sanctioned cross-app write chain:
`admissions.services.convert_to_enrollment` calls this on offer acceptance.

Every write binds `institution` for the duration of the call, exactly like
`classes_streams.services` — `TenantScopedModel`'s manager requires a bound
tenant to build the queryset `.create()` runs through, and binding
explicitly (rather than trusting whatever's ambiently bound) guarantees the
write happens under the same institution this function was actually asked
to act on, even if that ever diverges from ambient context.
"""

import datetime
import uuid

from apps.core.context import bind_institution
from apps.institutions.models import Institution
from apps.students.models import Enrollment, GuardianRelationship, Student


def create_student(
    *,
    institution: Institution,
    admission_number: str,
    first_name: str,
    last_name: str,
    date_of_birth: datetime.date | None = None,
    gender: str = "",
    user_id: uuid.UUID | None = None,
) -> Student:
    with bind_institution(institution):
        return Student.objects.create(
            institution_id=institution.id,
            admission_number=admission_number,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            gender=gender,
            user_id=user_id,
        )


def enroll_student(
    *,
    institution: Institution,
    student: Student,
    class_grade_id: uuid.UUID,
    term_id: uuid.UUID,
    stream_id: uuid.UUID | None = None,
    status: str = Enrollment.Status.ACTIVE,
) -> Enrollment:
    with bind_institution(institution):
        return Enrollment.objects.create(
            institution_id=institution.id,
            student=student,
            class_grade_id=class_grade_id,
            stream_id=stream_id,
            term_id=term_id,
            status=status,
        )


def add_guardian(
    *,
    institution: Institution,
    student: Student,
    guardian_user_id: uuid.UUID,
    relationship_type: str,
    is_primary_contact: bool = False,
) -> GuardianRelationship:
    if relationship_type not in GuardianRelationship.RelationshipType.values:
        raise ValueError(f"Unknown relationship type: {relationship_type!r}")
    with bind_institution(institution):
        return GuardianRelationship.objects.create(
            institution_id=institution.id,
            student=student,
            guardian_user_id=guardian_user_id,
            relationship_type=relationship_type,
            is_primary_contact=is_primary_contact,
        )

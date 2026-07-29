"""Public read interface for `students` — docs/modules.md.
`get_guardian_children` is the Parent-role object-scope selector
docs/permissions.md §3 requires ("only their own children") — consumed by
`views.py`'s queryset scoping, not just exposed for other apps.
"""

import uuid

from apps.students.models import Enrollment, Student


def get_active_roster(class_grade_id: uuid.UUID):
    """Students with an active enrollment in the given class grade —
    relies on the ambient tenant binding (`TenantMiddleware`), like every
    other selector here; only `classes_streams.get_current_term` needs the
    explicit-institution-argument treatment, since it's the one selector
    documented to also run from a Celery task with nothing ambiently bound.
    """
    return Student.objects.filter(
        enrollments__class_grade_id=class_grade_id,
        enrollments__status=Enrollment.Status.ACTIVE,
    ).distinct()


def get_guardian_children(guardian_user_id: uuid.UUID):
    return Student.objects.filter(
        guardian_relationships__guardian_user_id=guardian_user_id
    ).distinct()


def get_active_enrollment(student: Student, term_id: uuid.UUID) -> Enrollment | None:
    return Enrollment.objects.filter(
        student=student, term_id=term_id, status=Enrollment.Status.ACTIVE
    ).first()


def get_student_by_user_id(user_id: uuid.UUID) -> Student | None:
    return Student.objects.filter(user_id=user_id).first()

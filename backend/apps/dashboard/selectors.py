"""Public read interface for `dashboard` — docs/modules.md: "A facade over
selectors from many apps, tailored per portal." No models of its own —
every function here composes selectors other apps already expose, the same
Layer 3 "reads broadly, writes nothing" role `analytics`/`reports` share.
"""

import uuid

from apps.analytics.selectors import get_institution_summary
from apps.attendance.models import AttendanceRecord
from apps.attendance.selectors import get_attendance_rate
from apps.core.context import bind_institution
from apps.documents.selectors import get_documents_for
from apps.finance.selectors import get_balance
from apps.institutions.models import Institution
from apps.students.models import Student
from apps.students.selectors import get_guardian_children
from apps.timetable.selectors import get_staff_schedule


def get_principal_dashboard(institution: Institution, term_id: uuid.UUID) -> dict:
    return get_institution_summary(institution, term_id)


def get_teacher_dashboard(institution: Institution, staff_id: uuid.UUID) -> dict:
    assignments = get_staff_schedule(institution, staff_id)
    return {
        "schedule": [
            {
                "day_of_week": assignment.period.day_of_week,
                "start_time": assignment.period.start_time,
                "end_time": assignment.period.end_time,
                "subject_id": assignment.subject_id,
                "room": assignment.room,
            }
            for assignment in assignments
        ]
    }


def get_parent_dashboard(
    institution: Institution, guardian_user_id: uuid.UUID, term_id: uuid.UUID
) -> dict:
    # `get_guardian_children` relies on ambient tenant binding rather than
    # self-binding (same shape as `students.selectors.get_active_roster`),
    # so this self-binds — this function has no guarantee of a request's
    # ambient bind, the same "documented to also run outside a request"
    # reasoning `reports.services.generate_report_card` applies.
    with bind_institution(institution):
        children = list(get_guardian_children(guardian_user_id))
    return {
        "children": [
            {
                "student_id": child.id,
                "admission_number": child.admission_number,
                "first_name": child.first_name,
                "last_name": child.last_name,
                "balance": get_balance(institution, child.id, term_id),
            }
            for child in children
        ]
    }


def get_student_dashboard(institution: Institution, student: Student, term_id: uuid.UUID) -> dict:
    rate = get_attendance_rate(
        institution, AttendanceRecord.SubjectType.STUDENT, student.id, term_id
    )
    balance = get_balance(institution, student.id, term_id)
    documents = get_documents_for(institution, student)
    return {
        "attendance_rate": rate,
        "balance": balance,
        "documents": [
            {"id": document.id, "minio_object_key": document.minio_object_key}
            for document in documents
        ],
    }

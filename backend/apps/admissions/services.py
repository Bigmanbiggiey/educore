"""Public write interface for `admissions` — docs/modules.md.

`convert_to_enrollment` is the one sanctioned cross-app write chain in
Layer 1: it calls `students.services.create_student`/`enroll_student`
directly, the only place any Layer 1 sibling is allowed to mutate
`students`' state (docs/modules.md's `parents` entry reads guardian links
from `students`; this is the one that *writes*).

Every write here binds `institution` for the duration of the call, same
reasoning as every other Layer 1 app's services.py, and every stage
transition appends an `ApplicationStage` history row rather than only
updating `Application.stage` in place — the current value is denormalized
for fast filtering, but the transition history is real audit-relevant data.
"""

import datetime
import uuid

from django.db import transaction
from django.utils import timezone

from apps.admissions.models import Application, ApplicationStage, Offer
from apps.core.context import bind_institution
from apps.institutions.models import Institution
from apps.students.models import Enrollment
from apps.students.services import create_student, enroll_student


def submit_application(
    *, institution: Institution, applicant_details: dict, term_applying_for_id: uuid.UUID
) -> Application:
    with bind_institution(institution):
        application = Application.objects.create(
            institution_id=institution.id,
            applicant_details=applicant_details,
            term_applying_for_id=term_applying_for_id,
        )
        ApplicationStage.objects.create(
            institution_id=institution.id,
            application=application,
            stage=Application.Stage.SUBMITTED,
        )
    return application


@transaction.atomic
def make_offer(*, institution: Institution, application: Application) -> Offer:
    with bind_institution(institution):
        offer = Offer.objects.create(
            institution_id=institution.id, application=application, offered_at=timezone.now()
        )
        application.stage = Application.Stage.OFFERED
        application.save(update_fields=["stage", "updated_at"])
        ApplicationStage.objects.create(
            institution_id=institution.id, application=application, stage=Application.Stage.OFFERED
        )
    return offer


@transaction.atomic
def accept_offer(*, institution: Institution, offer: Offer) -> Offer:
    with bind_institution(institution):
        offer.accepted_at = timezone.now()
        offer.save(update_fields=["accepted_at", "updated_at"])
        application = offer.application
        application.stage = Application.Stage.ACCEPTED
        application.save(update_fields=["stage", "updated_at"])
        ApplicationStage.objects.create(
            institution_id=institution.id, application=application, stage=Application.Stage.ACCEPTED
        )
    return offer


@transaction.atomic
def convert_to_enrollment(
    *,
    institution: Institution,
    application: Application,
    admission_number: str,
    class_grade_id: uuid.UUID,
    term_id: uuid.UUID,
    stream_id: uuid.UUID | None = None,
) -> Enrollment:
    if application.stage != Application.Stage.ACCEPTED:
        raise ValueError(
            f"Application {application.id} must be accepted before it can be "
            f"converted to an enrollment (current stage: {application.stage!r})."
        )
    details = application.applicant_details
    student = create_student(
        institution=institution,
        admission_number=admission_number,
        first_name=details.get("first_name", ""),
        last_name=details.get("last_name", ""),
        date_of_birth=_parse_date(details.get("date_of_birth")),
        gender=details.get("gender", ""),
    )
    enrollment = enroll_student(
        institution=institution,
        student=student,
        class_grade_id=class_grade_id,
        term_id=term_id,
        stream_id=stream_id,
    )
    with bind_institution(institution):
        application.stage = Application.Stage.ENROLLED
        application.save(update_fields=["stage", "updated_at"])
        ApplicationStage.objects.create(
            institution_id=institution.id, application=application, stage=Application.Stage.ENROLLED
        )
    return enrollment


def _parse_date(value: str | None) -> datetime.date | None:
    if not value:
        return None
    return datetime.date.fromisoformat(value)

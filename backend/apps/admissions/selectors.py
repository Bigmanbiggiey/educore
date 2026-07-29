"""Public read interface for `admissions` — docs/modules.md."""

import uuid

from apps.admissions.models import Application
from apps.core.context import bind_institution
from apps.institutions.models import Institution


def get_application(institution: Institution, application_id: uuid.UUID) -> Application | None:
    with bind_institution(institution):
        return Application.objects.filter(id=application_id).first()


def get_applications_by_stage(institution: Institution, stage: str):
    with bind_institution(institution):
        return list(Application.objects.filter(stage=stage))

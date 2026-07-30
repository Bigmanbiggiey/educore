"""Celery tasks owned by `curriculum_university` — docs/project-structure.md
§3. Thin wrapper: real logic lives in `services.py`, same split
`notifications_core.tasks.dispatch_notification`/`curriculum_844.tasks`
already established.
"""

from celery import shared_task

from apps.curriculum_university import services
from apps.institutions.models import Institution


@shared_task
def recompute_gpa_task(institution_id: str, semester_id: str) -> None:
    institution = Institution.objects.get(id=institution_id)
    services.recompute_gpa_snapshots(institution=institution, semester_id=semester_id)

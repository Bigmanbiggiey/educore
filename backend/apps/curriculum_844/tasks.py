"""Celery tasks owned by `curriculum_844` — docs/project-structure.md §3.
Thin wrapper: real logic lives in `services.py`, same split
`notifications_core.tasks.dispatch_notification` already established.
"""

from celery import shared_task

from apps.curriculum_844 import services
from apps.institutions.models import Institution


@shared_task
def recompute_mean_grades_task(institution_id: str, term_id: str, class_grade_id: str) -> None:
    institution = Institution.objects.get(id=institution_id)
    services.recompute_mean_grade_snapshots(
        institution=institution, term_id=term_id, class_grade_id=class_grade_id
    )

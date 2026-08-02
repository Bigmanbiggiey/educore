"""Celery tasks owned by `analytics` — docs/project-structure.md §3. Thin
wrappers: real logic lives in `services.py`, same split
`notifications_core.tasks.dispatch_notification`/`curriculum_844.tasks.
recompute_mean_grades_task` already established.
"""

from celery import shared_task

from apps.analytics import services
from apps.classes_streams.models import ClassGrade
from apps.classes_streams.selectors import get_current_term
from apps.core.context import bind_institution
from apps.institutions.models import Institution


@shared_task
def recompute_class_rollups_task(institution_id: str, class_grade_id: str, term_id: str) -> None:
    institution = Institution.objects.get(id=institution_id)
    with bind_institution(institution):
        class_grade = ClassGrade.objects.get(id=class_grade_id)
    services.compute_rollups(institution=institution, class_grade=class_grade, term_id=term_id)


@shared_task
def nightly_analytics_rollup() -> None:
    """Recomputes every class's rollups for every institution's current
    term, once a night (`CELERY_BEAT_SCHEDULE`) — same "loop every
    `Institution.objects.all()`, `bind_institution` per one, act" shape
    `communication.tasks.publish_due_announcements` established. A Beat
    task has no institution ambiently bound, so every institution's due
    work is checked, not just one."""
    for institution in Institution.objects.all():
        term = get_current_term(institution)
        if term is None:
            continue
        with bind_institution(institution):
            class_grades = list(ClassGrade.objects.filter(term=term))
        for class_grade in class_grades:
            services.compute_rollups(
                institution=institution, class_grade=class_grade, term_id=term.id
            )

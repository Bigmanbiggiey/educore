"""Celery tasks owned by `reports` — docs/project-structure.md §3. A batch
of PDF renders across a whole class is exactly the kind of slow work this
project already routes through Celery rather than a request — same "never
synchronously in a request" reasoning `notifications_core.services.send`
documents for its own case.
"""

from celery import shared_task

from apps.core.context import bind_institution
from apps.institutions.models import Institution
from apps.reports.services import generate_report_cards_for_roster
from apps.students.selectors import get_active_roster


@shared_task
def generate_class_report_cards_task(
    institution_id: str, class_grade_id: str, term_id: str
) -> None:
    institution = Institution.objects.get(id=institution_id)
    with bind_institution(institution):
        roster = list(get_active_roster(class_grade_id))
    generate_report_cards_for_roster(institution=institution, roster=roster, term_id=term_id)

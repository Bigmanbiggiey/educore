"""Public read interface for `transport` — docs/modules.md:
`selectors.get_route_manifest(...)`.
"""

import uuid
from collections import defaultdict

from apps.core.context import bind_institution
from apps.institutions.models import Institution
from apps.transport.models import Stop, TransportAssignment


def get_route_manifest(institution: Institution, route_id: uuid.UUID) -> list[dict]:
    """Stops on `route_id`, in `sequence` order, each with the student IDs
    assigned to board there — the driver's pickup manifest."""
    with bind_institution(institution):
        stops = list(Stop.objects.filter(route_id=route_id))
        assignments = TransportAssignment.objects.filter(route_id=route_id)
        students_by_stop = defaultdict(list)
        for assignment in assignments:
            students_by_stop[assignment.stop_id].append(assignment.student_id)
    return [
        {
            "stop_id": stop.id,
            "name": stop.name,
            "sequence": stop.sequence,
            "student_ids": students_by_stop[stop.id],
        }
        for stop in stops
    ]


def get_assignment_for_student(
    institution: Institution, student_id: uuid.UUID
) -> TransportAssignment | None:
    with bind_institution(institution):
        return TransportAssignment.objects.filter(student_id=student_id).first()

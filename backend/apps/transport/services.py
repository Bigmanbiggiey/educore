"""Public write interface for `transport` — docs/modules.md.

`create_vehicle`/`create_route`/`create_stop` are plain wrappers — none has
an invariant beyond its own columns, same "services.py is this app's
complete public write API" shape `classes_streams`/`timetable`/`inventory`
establish for their own plain-create models. `assign_transport` is
`update_or_create`-keyed on `student_id` — a student has at most one active
route/stop assignment (`transportassignment_one_per_student`), so
re-assigning corrects the row in place rather than duplicating it, same
idempotent-write pattern `clinic.set_health_record` established.
"""

import uuid

from apps.core.context import bind_institution
from apps.institutions.models import Institution
from apps.transport.models import Route, Stop, TransportAssignment, Vehicle


def create_vehicle(
    *,
    institution: Institution,
    registration_number: str,
    capacity: int,
    make_model: str = "",
    driver_name: str = "",
    driver_phone: str = "",
) -> Vehicle:
    with bind_institution(institution):
        return Vehicle.objects.create(
            institution_id=institution.id,
            registration_number=registration_number,
            capacity=capacity,
            make_model=make_model,
            driver_name=driver_name,
            driver_phone=driver_phone,
        )


def create_route(*, institution: Institution, vehicle: Vehicle, name: str) -> Route:
    with bind_institution(institution):
        return Route.objects.create(institution_id=institution.id, vehicle=vehicle, name=name)


def create_stop(*, institution: Institution, route: Route, name: str, sequence: int) -> Stop:
    with bind_institution(institution):
        return Stop.objects.create(
            institution_id=institution.id, route=route, name=name, sequence=sequence
        )


def assign_transport(
    *, institution: Institution, student_id: uuid.UUID, route: Route, stop: Stop
) -> TransportAssignment:
    with bind_institution(institution):
        assignment, _ = TransportAssignment.objects.update_or_create(
            institution_id=institution.id,
            student_id=student_id,
            defaults={"route": route, "stop": stop},
        )
    return assignment

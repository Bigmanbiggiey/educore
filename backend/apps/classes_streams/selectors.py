"""Public read interface for `classes_streams` — docs/modules.md.
`get_current_term` is the one function nearly every other Layer 1/2 app
calls rather than each computing "current term" from dates independently.

Every selector here takes `institution` explicitly and binds it for the
query via `bind_institution` (rather than relying on whatever tenant is
already ambiently bound) so these work correctly both inside a request
(`TenantMiddleware` already bound one) and from contexts with none bound at
all — a future Celery task, per docs/authentication.md §7's rule that
background jobs receive `institution_id` explicitly and re-derive
everything from it, never trusting ambient context. This still goes
through the ordinary structural `TenantManager` (`Model.objects`), not the
`all_tenants_unsafe` escape hatch, which is reserved for genuine
cross-tenant platform operations (docs/multitenancy.md §3).
"""

import uuid

from apps.classes_streams.models import ClassGrade, Term
from apps.core.context import bind_institution
from apps.institutions.models import Institution


def get_current_term(institution: Institution) -> Term | None:
    with bind_institution(institution):
        return Term.objects.filter(is_current=True).first()


def get_class_grade(institution: Institution, class_grade_id: uuid.UUID) -> ClassGrade | None:
    with bind_institution(institution):
        return ClassGrade.objects.filter(id=class_grade_id).first()


def get_term(institution: Institution, term_id: uuid.UUID) -> Term | None:
    with bind_institution(institution):
        return Term.objects.filter(id=term_id).first()

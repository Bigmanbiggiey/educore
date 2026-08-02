"""Public write interface for `reports` — docs/modules.md: "Orchestrates
report generation (PDF, via WeasyPrint or similar): pulls student data,
calls `academics.selectors.get_curriculum_engine(institution).
generate_report_data(...)`, pulls finance balance, renders, stores the
result via `documents.services.attach(...)`."

`generate_report_data`'s return shape is genuinely curriculum-specific
(each `curriculum_*` engine returns its own dict) — rather than five
bespoke per-curriculum PDF layouts (out of scope for "PDF generation" as
stated), the template renders one generic, curriculum-agnostic layout: a
student header plus a formatted dump of whatever the engine returned.
"""

import json
import uuid

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.template.loader import render_to_string
from weasyprint import HTML

from apps.academics.selectors import get_curriculum_engine, get_curriculum_type_for_student
from apps.core.context import bind_institution
from apps.documents.models import Document
from apps.documents.services import attach
from apps.finance.selectors import get_balance
from apps.institutions.models import Institution
from apps.students.models import Student
from apps.students.selectors import get_student_by_id


def generate_report_card(
    *, institution: Institution, student_id: uuid.UUID, term_id: uuid.UUID
) -> Document:
    # Self-binding, like `curriculum_844.services.recompute_mean_grade_snapshots`
    # — this is documented to also run from `tasks.generate_class_report_
    # cards_task`, with nothing ambiently bound the way a request has. The
    # curriculum engine's own `generate_report_data` (each `curriculum_*`
    # app's own selectors) also relies on ambient binding rather than
    # self-binding, so the whole pipeline needs to run under one bind, not
    # just the first lookup.
    with bind_institution(institution):
        student = get_student_by_id(student_id)
        if student is None:
            raise ValueError(f"No student matches id {student_id!r}.")

        curriculum_type = get_curriculum_type_for_student(institution, student, term_id)
        if curriculum_type is None:
            raise ValueError(
                f"Student {student_id} has no active enrollment for term {term_id!r}."
            )

        engine = get_curriculum_engine(institution, curriculum_type)
        data = engine.generate_report_data(
            institution=institution, student_id=student_id, term_id=term_id
        )
        balance = get_balance(institution, student_id, term_id)

    html = render_to_string(
        "reports/report_card.html",
        {
            "student": student,
            "term_id": term_id,
            "balance": balance,
            "data_json": json.dumps(data, indent=2, default=str),
        },
    )
    pdf_bytes = HTML(string=html).write_pdf()

    object_key = f"reports/{institution.id}/{student_id}/{term_id}.pdf"
    default_storage.save(object_key, ContentFile(pdf_bytes))

    return attach(
        institution=institution,
        minio_object_key=object_key,
        target=student,
        is_confidential=True,
    )


def generate_report_cards_for_roster(
    *, institution: Institution, roster: list[Student], term_id: uuid.UUID
) -> list[Document]:
    """Called by `tasks.generate_class_report_cards_task` — a plain loop,
    not `transaction.atomic()`: each report is an independent unit of work
    (PDF render + MinIO write + a `Document` row), and one student's
    failure shouldn't roll back every other student's already-generated
    report in the same batch."""
    return [
        generate_report_card(institution=institution, student_id=student.id, term_id=term_id)
        for student in roster
    ]

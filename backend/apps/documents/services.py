"""Public write interface for `documents` — docs/modules.md:
`services.attach(...)`. `create_category` is a plain wrapper — it has no
invariant beyond its own columns, same "public write API for this app's
tables" shape `classes_streams`/`timetable` establish for their own
plain-create models.

`attach` takes a real model instance for `target` (e.g. a `reports` caller
passing the `Student` it just generated a transcript PDF for) and resolves
the `ContentType`/object-id pair itself — the DRF view's own `create` can
still accept the raw `target_content_type`/`target_object_id` pair directly
from the client instead (see `views.py`), the same "services.py is the
cross-app write API, the app's own DRF view may use the generic path since
the client already supplies serializable field values" split
`documents`/`library`/`inventory` all share.
"""

from django.contrib.contenttypes.models import ContentType
from django.db import models

from apps.core.context import bind_institution
from apps.documents.models import Document, DocumentCategory
from apps.institutions.models import Institution


def create_category(
    *, institution: Institution, name: str, description: str = ""
) -> DocumentCategory:
    with bind_institution(institution):
        return DocumentCategory.objects.create(
            institution_id=institution.id, name=name, description=description
        )


def attach(
    *,
    institution: Institution,
    minio_object_key: str,
    target: models.Model,
    category: DocumentCategory | None = None,
    uploaded_by_id=None,
    is_confidential: bool = False,
) -> Document:
    with bind_institution(institution):
        return Document.objects.create(
            institution_id=institution.id,
            category=category,
            minio_object_key=minio_object_key,
            target_content_type=ContentType.objects.get_for_model(target),
            target_object_id=target.pk,
            uploaded_by_id=uploaded_by_id,
            is_confidential=is_confidential,
        )

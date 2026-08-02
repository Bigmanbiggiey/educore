"""Public read interface for `documents` — docs/modules.md:
`selectors.get_documents_for(target)` — used by `reports` to look up the
documents (e.g. previously generated PDFs) attached to a given model
instance.
"""

from django.contrib.contenttypes.models import ContentType
from django.db import models

from apps.core.context import bind_institution
from apps.documents.models import Document
from apps.institutions.models import Institution


def get_documents_for(institution: Institution, target: models.Model):
    with bind_institution(institution):
        content_type = ContentType.objects.get_for_model(target)
        return list(
            Document.objects.filter(target_content_type=content_type, target_object_id=target.pk)
        )

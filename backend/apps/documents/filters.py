"""Explicit filter whitelist for `documents.Document` — docs/api-design.md
§6: hand-declared, not auto-derived from `Meta.fields` (see
`attendance.filters`'s module docstring for the full explanation this
project reuses everywhere).
"""

import django_filters

from apps.documents.models import Document


class DocumentFilterSet(django_filters.FilterSet):
    category = django_filters.UUIDFilter(field_name="category_id")
    target_content_type = django_filters.NumberFilter(field_name="target_content_type_id")
    target_object_id = django_filters.UUIDFilter(field_name="target_object_id")
    is_confidential = django_filters.BooleanFilter(field_name="is_confidential")

    class Meta:
        model = Document
        fields = ["category", "target_content_type", "target_object_id", "is_confidential"]

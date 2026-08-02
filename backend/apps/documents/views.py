"""API views for `documents` — docs/api-design.md. `Document`/`DocumentCategory`
have no invariant beyond their own columns for the API's own create path
(the client supplies `target_content_type`/`target_object_id` directly), so
both go through the generic `TenantScopedModelViewSet` path — same as
`library.BookViewSet`/`CopyViewSet`.
"""

from api.viewsets import TenantScopedModelViewSet
from apps.documents.filters import DocumentFilterSet
from apps.documents.models import Document, DocumentCategory
from apps.documents.serializers import DocumentCategorySerializer, DocumentSerializer
from apps.permissions.permissions import HasPermission, IsInstitutionMember

_WRITE_ACTIONS = ("create", "update", "partial_update", "destroy")


def _write_gated_by(permission_code):
    def get_permissions(self):
        if self.action in _WRITE_ACTIONS:
            return [IsInstitutionMember(), HasPermission(permission_code)()]
        return [IsInstitutionMember()]

    return get_permissions


class DocumentCategoryViewSet(TenantScopedModelViewSet):
    queryset_model = DocumentCategory
    serializer_class = DocumentCategorySerializer
    get_permissions = _write_gated_by("documents.document_category.manage")


class DocumentViewSet(TenantScopedModelViewSet):
    queryset_model = Document
    serializer_class = DocumentSerializer
    filterset_class = DocumentFilterSet
    get_permissions = _write_gated_by("documents.document.manage")

"""API views for `classes_streams` — docs/api-design.md. Reads are open to
any active institution member (most roles need to read the current term/
class structure); writes require a permission code specific to the
resource, following `{app}.{resource}.{action}` (docs/permissions.md §1).
"""

from rest_framework.decorators import action
from rest_framework.response import Response

from api.viewsets import TenantScopedModelViewSet
from apps.classes_streams.models import (
    AcademicYear,
    ClassGrade,
    ClassTeacherAssignment,
    Stream,
    Term,
)
from apps.classes_streams.serializers import (
    AcademicYearSerializer,
    ClassGradeSerializer,
    ClassTeacherAssignmentSerializer,
    StreamSerializer,
    TermSerializer,
)
from apps.classes_streams.services import set_current_term
from apps.permissions.permissions import HasPermission, IsInstitutionMember

_WRITE_ACTIONS = ("create", "update", "partial_update", "destroy")


def _write_gated_by(permission_code):
    """Returns a `get_permissions` method: any active member may read,
    only a member holding `permission_code` may write."""

    def get_permissions(self):
        if self.action in _WRITE_ACTIONS:
            return [IsInstitutionMember(), HasPermission(permission_code)()]
        return [IsInstitutionMember()]

    return get_permissions


class AcademicYearViewSet(TenantScopedModelViewSet):
    queryset_model = AcademicYear
    serializer_class = AcademicYearSerializer
    get_permissions = _write_gated_by("classes_streams.academic_year.manage")


class TermViewSet(TenantScopedModelViewSet):
    queryset_model = Term
    serializer_class = TermSerializer
    # No `filterset_fields` — django-filter's automatic field-type
    # resolution calls `model_field.model._default_manager.all().query`
    # directly (bypassing any view-level fix), which needs a bound tenant
    # that doesn't exist during `manage.py spectacular`'s schema
    # generation. An explicit `django_filters.FilterSet` subclass (filters
    # declared by hand, not auto-derived from `Meta.fields`) avoids this
    # and is the correct way to add filtering here later.

    def get_permissions(self):
        if self.action in (*_WRITE_ACTIONS, "set_current"):
            return [IsInstitutionMember(), HasPermission("classes_streams.term.manage")()]
        return [IsInstitutionMember()]

    @action(detail=True, methods=["post"], url_path="set-current")
    def set_current(self, request, pk=None):
        term = self.get_object()
        set_current_term(institution=request.institution, term=term)
        return Response(self.get_serializer(term).data)


class ClassGradeViewSet(TenantScopedModelViewSet):
    queryset_model = ClassGrade
    serializer_class = ClassGradeSerializer
    # See TermViewSet — no auto `filterset_fields`, same reason.
    get_permissions = _write_gated_by("classes_streams.class_grade.manage")


class StreamViewSet(TenantScopedModelViewSet):
    queryset_model = Stream
    serializer_class = StreamSerializer
    get_permissions = _write_gated_by("classes_streams.stream.manage")


class ClassTeacherAssignmentViewSet(TenantScopedModelViewSet):
    queryset_model = ClassTeacherAssignment
    serializer_class = ClassTeacherAssignmentSerializer
    get_permissions = _write_gated_by("classes_streams.class_teacher_assignment.manage")

"""API views for `academics` — docs/api-design.md. `GradingScale` and
`SubjectCatalog` get ordinary CRUD endpoints. `AssessmentRecordView`/
`ReportCardView` are the curriculum-agnostic pair docs/api-design.md §8
describes: genuinely shared operations get one endpoint that resolves the
active curriculum server-side via `selectors.get_curriculum_engine`, rather
than forcing a client to know which of several curriculum-specific URL
sets to call. Curriculum-specific fields ride in a `details` sub-object the
resolved engine validates itself.
"""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.viewsets import TenantScopedModelViewSet
from apps.academics.models import GradingScale, SubjectCatalog
from apps.academics.selectors import get_curriculum_engine, get_curriculum_type_for_student
from apps.academics.serializers import GradingScaleSerializer, SubjectCatalogSerializer
from apps.permissions.permissions import HasPermission, IsInstitutionMember
from apps.permissions.selectors import get_membership_access
from apps.students.selectors import get_guardian_children, get_student_by_id

_WRITE_ACTIONS = ("create", "update", "partial_update", "destroy")


def _write_gated_by(permission_code):
    def get_permissions(self):
        if self.action in _WRITE_ACTIONS:
            return [IsInstitutionMember(), HasPermission(permission_code)()]
        return [IsInstitutionMember()]

    return get_permissions


class GradingScaleViewSet(TenantScopedModelViewSet):
    queryset_model = GradingScale
    serializer_class = GradingScaleSerializer
    get_permissions = _write_gated_by("academics.grading_scale.manage")


class SubjectCatalogViewSet(TenantScopedModelViewSet):
    queryset_model = SubjectCatalog
    serializer_class = SubjectCatalogSerializer
    get_permissions = _write_gated_by("academics.subject_catalog.manage")


class _AssessmentRecordRequestSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    term_id = serializers.UUIDField()
    details = serializers.DictField()


def _resolve_student_and_curriculum_type(request, student_id, term_id):
    student = get_student_by_id(student_id)
    if student is None:
        raise NotFound("No student matches that id.")
    curriculum_type = get_curriculum_type_for_student(request.institution, student, term_id)
    if curriculum_type is None:
        raise NotFound("This student has no active enrollment for that term.")
    return student, curriculum_type


class AssessmentRecordView(APIView):
    """`POST /api/v1/assessments/` — records a single assessment result,
    regardless of which curriculum the target student's current enrollment
    runs. Writes only; reading a student's assessments back is part of the
    curriculum-specific report data below, since the shape of "an
    assessment" isn't itself cross-curriculum-shared the way this write
    operation is.
    """

    permission_classes = [IsInstitutionMember, HasPermission("academics.assessment.record")]

    @extend_schema(request=_AssessmentRecordRequestSerializer, responses={201: OpenApiTypes.OBJECT})
    def post(self, request):
        serializer = _AssessmentRecordRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        _student, curriculum_type = _resolve_student_and_curriculum_type(
            request, data["student_id"], data["term_id"]
        )
        engine = get_curriculum_engine(request.institution, curriculum_type)
        try:
            result = engine.record_assessment(
                institution=request.institution,
                student_id=data["student_id"],
                term_id=data["term_id"],
                details=data["details"],
            )
        except ValueError as exc:
            raise ValidationError({"details": [str(exc)]}) from exc
        return Response(result, status=201)


class ReportCardView(APIView):
    """`GET /api/v1/report-cards/<student_id>/<term_id>/` — object-scoped
    like `students.StudentViewSet`: a Parent may only pull their own
    child's report, a Student only their own, regardless of what broader
    permission either might also hold (fail-closed, docs/permissions.md
    §3). Any other active member may pull any student's report.
    """

    permission_classes = [IsAuthenticated, IsInstitutionMember]

    @extend_schema(responses={200: OpenApiTypes.OBJECT})
    def get(self, request, student_id, term_id):
        student, curriculum_type = _resolve_student_and_curriculum_type(
            request, student_id, term_id
        )
        access = get_membership_access(request.user, request.institution)
        if "Parent" in access.role_names:
            if not get_guardian_children(request.user.id).filter(id=student.id).exists():
                raise PermissionDenied("Not a guardian of this student.")
        elif "Student" in access.role_names:
            if student.user_id != request.user.id:
                raise PermissionDenied("Not your own record.")

        engine = get_curriculum_engine(request.institution, curriculum_type)
        data = engine.generate_report_data(
            institution=request.institution, student_id=student.id, term_id=term_id
        )
        return Response(data)

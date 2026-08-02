"""API views for `reports` — docs/api-design.md. `generate` is
object-scoped exactly like `academics.views.ReportCardView` (Parent → own
child, Student → own record, any other active member → any student) —
generating someone else's report card is exactly as sensitive as reading
one. `generate-class` is a staff-only batch action that enqueues the
Celery task rather than blocking a request on ~40 PDF renders.
"""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.permissions.permissions import HasPermission, IsInstitutionMember
from apps.permissions.selectors import get_membership_access
from apps.reports.serializers import (
    GenerateClassReportCardsRequestSerializer,
    GenerateReportCardRequestSerializer,
)
from apps.reports.services import generate_report_card
from apps.reports.tasks import generate_class_report_cards_task
from apps.students.selectors import get_guardian_children, get_student_by_id


class GenerateReportCardView(APIView):
    permission_classes = [IsAuthenticated, IsInstitutionMember]

    @extend_schema(
        request=GenerateReportCardRequestSerializer, responses={201: OpenApiTypes.OBJECT}
    )
    def post(self, request):
        serializer = GenerateReportCardRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        student = get_student_by_id(data["student_id"])
        if student is None:
            raise NotFound("No student matches that id.")

        access = get_membership_access(request.user, request.institution)
        if "Parent" in access.role_names:
            if not get_guardian_children(request.user.id).filter(id=student.id).exists():
                raise PermissionDenied("Not a guardian of this student.")
        elif "Student" in access.role_names:
            if student.user_id != request.user.id:
                raise PermissionDenied("Not your own record.")

        try:
            document = generate_report_card(
                institution=request.institution, student_id=student.id, term_id=data["term_id"]
            )
        except ValueError as exc:
            raise ValidationError({"detail": [str(exc)]}) from exc
        return Response(
            {"document_id": str(document.id), "minio_object_key": document.minio_object_key},
            status=201,
        )


class GenerateClassReportCardsView(APIView):
    permission_classes = [IsInstitutionMember, HasPermission("reports.report_card.generate_class")]

    @extend_schema(
        request=GenerateClassReportCardsRequestSerializer, responses={202: OpenApiTypes.OBJECT}
    )
    def post(self, request):
        serializer = GenerateClassReportCardsRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        generate_class_report_cards_task.delay(
            str(request.institution.id), str(data["class_grade_id"]), str(data["term_id"])
        )
        return Response({"detail": "Report card generation enqueued."}, status=202)

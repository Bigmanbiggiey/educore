"""API views for `dashboard` — docs/api-design.md. Each view resolves data
for *the calling user only* — a Teacher sees their own schedule, a Parent
their own children, a Student their own record — fail-closed the same way
`students.StudentViewSet`/`parents.ParentProfileViewSet` self-scope
regardless of any broader permission held (docs/permissions.md §3).
`?term_id=` is optional on the term-scoped views; omitted, it falls back to
the institution's current term.
"""

from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.classes_streams.selectors import get_current_term
from apps.dashboard.selectors import (
    get_parent_dashboard,
    get_principal_dashboard,
    get_student_dashboard,
    get_teacher_dashboard,
)
from apps.dashboard.serializers import (
    ParentDashboardSerializer,
    PrincipalDashboardSerializer,
    StudentDashboardSerializer,
    TeacherDashboardSerializer,
)
from apps.permissions.permissions import HasRole, IsInstitutionMember
from apps.staff.selectors import get_staff_by_user_id
from apps.students.selectors import get_student_by_user_id


def _resolve_term_id(request):
    term_id = request.query_params.get("term_id")
    if term_id:
        return term_id
    term = get_current_term(request.institution)
    if term is None:
        raise NotFound("This institution has no current term set.")
    return term.id


class PrincipalDashboardView(APIView):
    permission_classes = [
        IsInstitutionMember,
        HasRole("Institution Administrator", "Principal", "Deputy Principal"),
    ]

    @extend_schema(responses={200: PrincipalDashboardSerializer})
    def get(self, request):
        data = get_principal_dashboard(request.institution, _resolve_term_id(request))
        return Response(PrincipalDashboardSerializer(data).data)


class TeacherDashboardView(APIView):
    permission_classes = [IsInstitutionMember, HasRole("Teacher")]

    @extend_schema(responses={200: TeacherDashboardSerializer})
    def get(self, request):
        staff = get_staff_by_user_id(request.user.id)
        if staff is None:
            raise NotFound("No staff profile for this user.")
        data = get_teacher_dashboard(request.institution, staff.id)
        return Response(TeacherDashboardSerializer(data).data)


class ParentDashboardView(APIView):
    permission_classes = [IsInstitutionMember, HasRole("Parent")]

    @extend_schema(responses={200: ParentDashboardSerializer})
    def get(self, request):
        data = get_parent_dashboard(request.institution, request.user.id, _resolve_term_id(request))
        return Response(ParentDashboardSerializer(data).data)


class StudentDashboardView(APIView):
    permission_classes = [IsInstitutionMember, HasRole("Student")]

    @extend_schema(responses={200: StudentDashboardSerializer})
    def get(self, request):
        student = get_student_by_user_id(request.user.id)
        if student is None:
            raise NotFound("No student record for this user.")
        data = get_student_dashboard(request.institution, student, _resolve_term_id(request))
        return Response(StudentDashboardSerializer(data).data)

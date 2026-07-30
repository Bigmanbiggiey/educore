"""API views for `curriculum_university` — docs/api-design.md §8.
`Faculty`/`School`/`UniversityDepartment`/`Programme`/`Unit`/`Semester`/
`CourseRegistration`/`Dissertation`/`Graduation` all get ordinary CRUD (the
last two have no cross-curriculum equivalent, same non-object-scoped
precedent as `curriculum_cbc.Project`). `recompute-gpa` enqueues the Celery
task, same shape as `curriculum_844`'s `recompute-mean-grades`. Unit
assessment recording does NOT get its own endpoint here — that's
`academics.views.AssessmentRecordView`.
"""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from api.viewsets import TenantScopedModelViewSet
from apps.curriculum_university.models import (
    CourseRegistration,
    Dissertation,
    Faculty,
    Graduation,
    Programme,
    School,
    Semester,
    Unit,
    UniversityDepartment,
)
from apps.curriculum_university.serializers import (
    CourseRegistrationSerializer,
    DissertationSerializer,
    FacultySerializer,
    GraduationSerializer,
    ProgrammeSerializer,
    RecomputeGpaRequestSerializer,
    SchoolSerializer,
    SemesterSerializer,
    UnitSerializer,
    UniversityDepartmentSerializer,
)
from apps.curriculum_university.tasks import recompute_gpa_task
from apps.permissions.permissions import HasPermission, IsInstitutionMember

_WRITE_ACTIONS = ("create", "update", "partial_update", "destroy")


def _write_gated_by(permission_code):
    def get_permissions(self):
        if self.action in _WRITE_ACTIONS:
            return [IsInstitutionMember(), HasPermission(permission_code)()]
        return [IsInstitutionMember()]

    return get_permissions


class FacultyViewSet(TenantScopedModelViewSet):
    queryset_model = Faculty
    serializer_class = FacultySerializer
    get_permissions = _write_gated_by("curriculum_university.faculty.manage")


class SchoolViewSet(TenantScopedModelViewSet):
    queryset_model = School
    serializer_class = SchoolSerializer
    get_permissions = _write_gated_by("curriculum_university.school.manage")


class UniversityDepartmentViewSet(TenantScopedModelViewSet):
    queryset_model = UniversityDepartment
    serializer_class = UniversityDepartmentSerializer
    get_permissions = _write_gated_by("curriculum_university.department.manage")


class ProgrammeViewSet(TenantScopedModelViewSet):
    queryset_model = Programme
    serializer_class = ProgrammeSerializer
    get_permissions = _write_gated_by("curriculum_university.programme.manage")


class UnitViewSet(TenantScopedModelViewSet):
    queryset_model = Unit
    serializer_class = UnitSerializer
    get_permissions = _write_gated_by("curriculum_university.unit.manage")


class SemesterViewSet(TenantScopedModelViewSet):
    queryset_model = Semester
    serializer_class = SemesterSerializer
    get_permissions = _write_gated_by("curriculum_university.semester.manage")


class CourseRegistrationViewSet(TenantScopedModelViewSet):
    queryset_model = CourseRegistration
    serializer_class = CourseRegistrationSerializer
    get_permissions = _write_gated_by("curriculum_university.course_registration.manage")


class DissertationViewSet(TenantScopedModelViewSet):
    queryset_model = Dissertation
    serializer_class = DissertationSerializer
    get_permissions = _write_gated_by("curriculum_university.dissertation.manage")


class GraduationViewSet(TenantScopedModelViewSet):
    queryset_model = Graduation
    serializer_class = GraduationSerializer
    get_permissions = _write_gated_by("curriculum_university.graduation.manage")


class RecomputeGpaView(APIView):
    """Enqueues the Celery task that recomputes `GPASnapshot` for every
    student registered in a semester — GPA/CGPA need everyone recomputed
    together, so this is an explicit administrative action, not something
    that happens automatically on every `UnitAssessment` write."""

    permission_classes = [
        IsInstitutionMember,
        HasPermission("curriculum_university.gpa.recompute"),
    ]

    @extend_schema(request=RecomputeGpaRequestSerializer, responses={202: OpenApiTypes.OBJECT})
    def post(self, request):
        serializer = RecomputeGpaRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        recompute_gpa_task.delay(str(request.institution.id), str(data["semester_id"]))
        return Response({"detail": "Recompute enqueued."}, status=202)

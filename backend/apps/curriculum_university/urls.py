from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.curriculum_university.views import (
    CourseRegistrationViewSet,
    DissertationViewSet,
    FacultyViewSet,
    GraduationViewSet,
    ProgrammeViewSet,
    RecomputeGpaView,
    SchoolViewSet,
    SemesterViewSet,
    UnitViewSet,
    UniversityDepartmentViewSet,
)

app_name = "curriculum_university"

router = DefaultRouter()
router.register("faculties", FacultyViewSet, basename="faculty")
router.register("schools", SchoolViewSet, basename="school")
router.register("departments", UniversityDepartmentViewSet, basename="department")
router.register("programmes", ProgrammeViewSet, basename="programme")
router.register("units", UnitViewSet, basename="unit")
router.register("semesters", SemesterViewSet, basename="semester")
router.register("course-registrations", CourseRegistrationViewSet, basename="course-registration")
router.register("dissertations", DissertationViewSet, basename="dissertation")
router.register("graduations", GraduationViewSet, basename="graduation")

urlpatterns = [
    *router.urls,
    path("recompute-gpa/", RecomputeGpaView.as_view(), name="recompute-gpa"),
]

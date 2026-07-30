from django.contrib import admin

from apps.curriculum_university.models import (
    CourseRegistration,
    Dissertation,
    Faculty,
    GPASnapshot,
    Graduation,
    Programme,
    School,
    Semester,
    Unit,
    UnitAssessment,
    UniversityDepartment,
)


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ("name", "institution_id")


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("name", "faculty")


@admin.register(UniversityDepartment)
class UniversityDepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "school")


@admin.register(Programme)
class ProgrammeAdmin(admin.ModelAdmin):
    list_display = ("name", "programme_code", "degree_level", "department")
    list_filter = ("degree_level",)


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("name", "unit_code", "programme", "credit_hours", "semester_offered")


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ("name", "number", "term_id")


@admin.register(CourseRegistration)
class CourseRegistrationAdmin(admin.ModelAdmin):
    list_display = ("student_id", "unit", "semester", "status")
    list_filter = ("status",)


@admin.register(UnitAssessment)
class UnitAssessmentAdmin(admin.ModelAdmin):
    list_display = ("unit", "student_id", "semester", "assessment_type", "score", "max_score")
    list_filter = ("assessment_type",)


@admin.register(GPASnapshot)
class GPASnapshotAdmin(admin.ModelAdmin):
    list_display = ("student_id", "semester", "gpa", "cgpa")


@admin.register(Dissertation)
class DissertationAdmin(admin.ModelAdmin):
    list_display = ("title", "student_id", "supervisor_id", "status")
    list_filter = ("status",)


@admin.register(Graduation)
class GraduationAdmin(admin.ModelAdmin):
    list_display = ("student_id", "programme", "conferred_at", "classification")

from django.contrib import admin

from apps.students.models import Enrollment, GuardianRelationship, Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("admission_number", "first_name", "last_name", "institution_id")
    search_fields = ("admission_number", "first_name", "last_name")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "class_grade_id", "stream_id", "term_id", "status")
    list_filter = ("status",)


@admin.register(GuardianRelationship)
class GuardianRelationshipAdmin(admin.ModelAdmin):
    list_display = ("student", "guardian_user_id", "relationship_type", "is_primary_contact")
    list_filter = ("relationship_type", "is_primary_contact")

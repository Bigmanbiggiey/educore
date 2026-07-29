from django.contrib import admin

from apps.staff.models import StaffProfile


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ("employee_number", "first_name", "last_name", "department", "employment_type")
    list_filter = ("department", "employment_type")
    search_fields = ("employee_number", "first_name", "last_name")

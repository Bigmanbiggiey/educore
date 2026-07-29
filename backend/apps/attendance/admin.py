from django.contrib import admin

from apps.attendance.models import AttendanceRecord


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("subject_type", "target_id", "date", "status")
    list_filter = ("subject_type", "status")

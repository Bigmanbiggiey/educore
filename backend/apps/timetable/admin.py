from django.contrib import admin

from apps.timetable.models import Period, SubjectSlotAssignment, Timetable


@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ("id", "institution_id", "term_id", "class_grade_id")


@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    list_display = ("timetable", "day_of_week", "start_time", "end_time")
    list_filter = ("day_of_week",)


@admin.register(SubjectSlotAssignment)
class SubjectSlotAssignmentAdmin(admin.ModelAdmin):
    list_display = ("period", "subject_id", "staff_id", "room")

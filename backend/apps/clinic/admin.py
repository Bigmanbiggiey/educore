from django.contrib import admin

from apps.clinic.models import ClinicVisit, HealthRecord, Medication


@admin.register(HealthRecord)
class HealthRecordAdmin(admin.ModelAdmin):
    list_display = ("student_id", "blood_group")


@admin.register(ClinicVisit)
class ClinicVisitAdmin(admin.ModelAdmin):
    list_display = ("student_id", "visit_date", "treated_by_id")
    list_filter = ("visit_date",)


@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ("name", "dosage", "visit")

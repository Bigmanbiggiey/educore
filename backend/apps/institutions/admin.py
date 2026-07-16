from django.contrib import admin

from apps.institutions.models import (
    AcademicCalendarSettings,
    Domain,
    Institution,
    InstitutionCurriculum,
)


class DomainInline(admin.TabularInline):
    model = Domain
    extra = 0


class InstitutionCurriculumInline(admin.TabularInline):
    model = InstitutionCurriculum
    extra = 0


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "isolation_tier", "is_active", "created_at")
    list_filter = ("isolation_tier", "is_active")
    search_fields = ("name", "slug")
    inlines = [DomainInline, InstitutionCurriculumInline]


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ("hostname", "institution", "domain_type", "is_primary", "verified_at")
    list_filter = ("domain_type",)
    search_fields = ("hostname",)


@admin.register(AcademicCalendarSettings)
class AcademicCalendarSettingsAdmin(admin.ModelAdmin):
    list_display = ("institution", "academic_year_start_month", "terms_per_year")

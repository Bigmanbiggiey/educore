from django.contrib import admin

from apps.parents.models import ParentProfile


@admin.register(ParentProfile)
class ParentProfileAdmin(admin.ModelAdmin):
    list_display = ("user_id", "institution_id", "preferred_language")

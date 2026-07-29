from django.contrib import admin

from apps.permissions.models import (
    InstitutionMembership,
    MembershipRole,
    Permission,
    Role,
    RolePermission,
)


class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 0


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "institution", "is_system")
    list_filter = ("is_system",)
    search_fields = ("name",)
    inlines = [RolePermissionInline]


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("code", "scope", "description")
    list_filter = ("scope",)
    search_fields = ("code",)


class MembershipRoleInline(admin.TabularInline):
    model = MembershipRole
    extra = 0


@admin.register(InstitutionMembership)
class InstitutionMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "institution", "status", "is_default")
    list_filter = ("status",)
    search_fields = ("user__email", "user__phone", "institution__name")
    inlines = [MembershipRoleInline]

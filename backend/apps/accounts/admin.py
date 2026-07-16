from django.contrib import admin

from apps.accounts.models import PasswordResetToken, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    # Not django.contrib.auth.admin.UserAdmin — its fieldsets assume
    # username/first_name/last_name/groups, none of which this model has.
    list_display = ("email", "phone", "is_platform_staff", "is_active", "date_joined")
    list_filter = ("is_platform_staff", "is_active")
    search_fields = ("email", "phone")
    readonly_fields = ("date_joined", "last_login")
    # Never edit the password hash directly — use the reset flow or
    # `manage.py changepassword`.
    exclude = ("password",)


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "expires_at", "used_at", "created_at")
    readonly_fields = ("token",)

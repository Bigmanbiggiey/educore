"""Seeds the platform-default `NotificationTemplate` row
`apps.permissions.services.invite_member` needs — mirrors
`0002_seed_institution_admin_welcome_template.py`'s exact reasoning and
shape, for the same failure mode: without a platform-default
`(key, channel)` row, `notifications_core.selectors.get_template` raises
`NotificationTemplate.DoesNotExist`, logged as a `FAILED` `NotificationLog`
rather than a crash, but still a silently-broken welcome email. Generic,
role-agnostic copy (`$role_name`) since one template now serves all 11
invitable roles, unlike the institution-admin-specific one.
"""

from django.db import migrations

TEMPLATE_KEY = "member_welcome"


def seed_template(apps, schema_editor):
    NotificationTemplate = apps.get_model("notifications_core", "NotificationTemplate")
    NotificationTemplate.objects.create(
        institution=None,
        key=TEMPLATE_KEY,
        channel="email",
        subject_template="Welcome to EduCore, $institution_name",
        body_template=(
            "Your EduCore $role_name account for $institution_name has been created.\n\n"
            "Set your password to get started: $reset_url"
        ),
    )


def unseed_template(apps, schema_editor):
    NotificationTemplate = apps.get_model("notifications_core", "NotificationTemplate")
    NotificationTemplate.objects.filter(
        institution__isnull=True, key=TEMPLATE_KEY, channel="email"
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("notifications_core", "0002_seed_institution_admin_welcome_template"),
    ]

    operations = [
        migrations.RunPython(seed_template, unseed_template),
    ]

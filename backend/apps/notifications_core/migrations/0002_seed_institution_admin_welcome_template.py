"""Seeds the platform-default `NotificationTemplate` row
`apps.permissions.services.provision_institution_admin` needs — without a
platform-default `(key, channel)` row, `notifications_core.selectors.get_template`
raises `NotificationTemplate.DoesNotExist` (logged as a `FAILED`
`NotificationLog` by `tasks.dispatch_notification`, not a crash, but still
a silently-broken welcome email). Mirrors
`apps.communication.migrations.0002_seed_notification_templates`'s
seeding pattern. Only the `email` channel is needed — the institution-admin
welcome notification is always dispatched with `channel="email"`.
"""

from django.db import migrations

TEMPLATE_KEY = "institution_admin_welcome"


def seed_template(apps, schema_editor):
    NotificationTemplate = apps.get_model("notifications_core", "NotificationTemplate")
    NotificationTemplate.objects.create(
        institution=None,
        key=TEMPLATE_KEY,
        channel="email",
        subject_template="Welcome to EduCore, $institution_name",
        body_template=(
            "Your EduCore administrator account for $institution_name has been created.\n\n"
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
        ("notifications_core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_template, unseed_template),
    ]

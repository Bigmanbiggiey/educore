"""Seeds the platform-default `NotificationTemplate` rows
`services.publish_announcement` needs — `notifications_core.selectors.get_template`
raises `NotificationTemplate.DoesNotExist` (logged as a `FAILED`
`NotificationLog` by `tasks.dispatch_notification`, not a crash, but still
a silently-broken fan-out) if no platform-default row exists for a given
`(key, channel)` and the institution hasn't overridden it either. One row
per `notifications_core.Channel` value, since `Announcement.channels` is a
free-form per-institution choice — whichever channel is picked must
resolve.

Cross-app data migration (seeds a `notifications_core` row from a
`communication` migration) — a new but sanctioned use of Django's
migration-dependency mechanism: this migration depends on
`("notifications_core", "0001_initial")` so the table exists first,
exactly what that dependency declaration is for.
"""

from django.db import migrations

TEMPLATE_KEY = "communication.announcement.published"


def seed_templates(apps, schema_editor):
    NotificationTemplate = apps.get_model("notifications_core", "NotificationTemplate")
    NotificationTemplate.objects.bulk_create(
        [
            NotificationTemplate(
                institution=None,
                key=TEMPLATE_KEY,
                channel="sms",
                subject_template="",
                body_template="$title: $body",
            ),
            NotificationTemplate(
                institution=None,
                key=TEMPLATE_KEY,
                channel="email",
                subject_template="$title",
                body_template="$body",
            ),
            NotificationTemplate(
                institution=None,
                key=TEMPLATE_KEY,
                channel="push",
                subject_template="$title",
                body_template="$body",
            ),
        ]
    )


def unseed_templates(apps, schema_editor):
    NotificationTemplate = apps.get_model("notifications_core", "NotificationTemplate")
    NotificationTemplate.objects.filter(institution__isnull=True, key=TEMPLATE_KEY).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("communication", "0001_initial"),
        ("notifications_core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_templates, unseed_templates),
    ]

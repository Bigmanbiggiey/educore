from django.apps import AppConfig


class NotificationsCoreConfig(AppConfig):
    name = "apps.notifications_core"

    def ready(self):
        from apps.notifications_core import receivers  # noqa: F401

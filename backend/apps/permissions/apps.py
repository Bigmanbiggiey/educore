from django.apps import AppConfig


class PermissionsConfig(AppConfig):
    name = "apps.permissions"

    def ready(self):
        from apps.permissions import receivers  # noqa: F401

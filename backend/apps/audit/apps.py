from django.apps import AppConfig


class AuditConfig(AppConfig):
    name = "apps.audit"

    def ready(self):
        from apps.audit import receivers  # noqa: F401

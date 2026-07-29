# Ensures config.celery's app is loaded whenever Django starts, so
# `@shared_task` (used by every app's tasks.py, per docs/project-structure.md
# §3) binds to our configured Celery app rather than falling back to an
# unconfigured default one — the standard Celery+Django wiring
# (https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html).
from .celery import app as celery_app

__all__ = ("celery_app",)

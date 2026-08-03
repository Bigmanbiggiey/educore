"""Public write interface for `audit` — docs/modules.md. This is the *only*
sanctioned way any app records an audit entry: wired in via signals on
sensitive models (finance transactions, grade changes, role assignments)
once those exist, never called ad hoc from a random call site, so logging
isn't optional per code path.
"""

from django.contrib.contenttypes.models import ContentType
from django.db import models

from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.institutions.models import Institution


def log_action(
    *,
    actor: User | None,
    institution: Institution | None,
    action: str,
    target: models.Model | None = None,
    diff: dict | None = None,
    ip_address: str | None = None,
    acting_as_admin: bool = False,
) -> AuditLog:
    return AuditLog.objects.create(
        actor=actor,
        institution=institution,
        action=action,
        target_content_type=ContentType.objects.get_for_model(target) if target else None,
        target_object_id=target.pk if target else None,
        diff=diff or {},
        ip_address=ip_address,
        acting_as_admin=acting_as_admin,
    )

"""Connects `core.signals.audit_event` to `services.log_action` — the
sanctioned way another app (that can't import `apps.audit` directly,
e.g. a Layer-0 sibling) records an audit entry. Wired in `apps.py.ready()`.
"""

from django.dispatch import receiver

from apps.audit.services import log_action
from apps.core.signals import audit_event


@receiver(audit_event)
def handle_audit_event(
    sender,
    *,
    actor,
    institution,
    action,
    target=None,
    diff=None,
    ip_address=None,
    acting_as_admin=False,
    **kwargs,
):
    log_action(
        actor=actor,
        institution=institution,
        action=action,
        target=target,
        diff=diff,
        ip_address=ip_address,
        acting_as_admin=acting_as_admin,
    )

"""Connects `core.signals.institution_provisioned` to
`services.provision_institution_admin` — the sanctioned way `institutions`
(which can't import `permissions`, a forbidden reverse dependency under
`.importlinter`) triggers institution-admin provisioning. Wired in
`apps.py.ready()`, same pattern as `apps.audit.receivers`.
"""

from django.dispatch import receiver

from apps.core.signals import institution_provisioned
from apps.permissions.services import provision_institution_admin


@receiver(institution_provisioned)
def handle_institution_provisioned(
    sender, *, institution, admin_email, admin_phone=None, actor=None, **kwargs
):
    provision_institution_admin(
        institution=institution,
        admin_email=admin_email,
        admin_phone=admin_phone,
        actor=actor,
    )

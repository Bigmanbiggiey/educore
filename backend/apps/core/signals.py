"""Cross-app signals — live in `core` (the one layer every app depends on)
so a sender never needs a direct import of a sibling/higher-layer app it
can't legally import under `.importlinter`'s layer contract.
"""

import django.dispatch

# `apps.permissions`/`apps.audit` are declared independent siblings in
# `.importlinter` (same Layer 0 tier), so `permissions.views.ActAsView`
# sending an audit event can't import `apps.audit.services.log_action`
# directly — this is exactly the "wired in via signals... never called ad
# hoc from a random call site" integration `apps.audit.services.log_action`'s
# own docstring already calls for.
#
# Keyword args match `apps.audit.services.log_action`'s signature:
# actor, institution, action, target=None, diff=None, ip_address=None,
# acting_as_admin=False.
audit_event = django.dispatch.Signal()

# `apps.institutions` provisioned a new Institution and needs its first
# Institution Administrator seeded — but institutions/accounts are
# independent Layer 0 siblings (can't import accounts) and permissions
# sits above both, so this hands off to a receiver in `apps.permissions`,
# which legally imports both `apps.accounts` and `apps.institutions`.
#
# Keyword args: institution, admin_email, admin_phone=None, actor=None.
institution_provisioned = django.dispatch.Signal()

# `apps.permissions` needs to trigger a notification but can't import its
# Layer 0 sibling `apps.notifications_core` directly — same layer contract
# as above. Received by `apps.notifications_core.receivers`.
#
# Keyword args match `apps.notifications_core.services.send`'s signature
# exactly: institution, recipient, template_key, context, channel.
notification_requested = django.dispatch.Signal()

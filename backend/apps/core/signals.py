"""Cross-app audit signal — lives in `core` (the one layer every app
depends on) so a sender never needs a direct import of `apps.audit`
itself. `apps.permissions`/`apps.audit` are declared independent siblings
in `.importlinter` (same Layer 0 tier), so `permissions.views.ActAsView`
sending an audit event can't import `apps.audit.services.log_action`
directly — this is exactly the "wired in via signals... never called ad
hoc from a random call site" integration `apps.audit.services.log_action`'s
own docstring already calls for, just not yet exercised by anything.
"""

import django.dispatch

# Keyword args match `apps.audit.services.log_action`'s signature:
# actor, institution, action, target=None, diff=None, ip_address=None,
# acting_as_admin=False.
audit_event = django.dispatch.Signal()

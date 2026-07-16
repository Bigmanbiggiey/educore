"""Tenant-aware DB routing for the dedicated_db isolation tier —
docs/multitenancy.md §5.

Only touches `institution.isolation_tier`/`institution.db_alias` as plain
attributes on whatever `current_institution` holds — never imports
`apps.institutions.models.Institution` — so this lives in `core` without
creating a dependency on `institutions`.
"""

from apps.core.context import current_institution

# Layer 0 apps always migrate to `default` only, regardless of any
# tenant's isolation tier — Layer 0 is platform identity/tenancy-root data,
# never sharded per tenant (docs/multitenancy.md §4). Listed here in full
# even though only `core`/`institutions` exist yet, so this doesn't need
# revisiting as each remaining Layer 0 app lands.
PLATFORM_APPS = {
    "core",
    "institutions",
    "accounts",
    "permissions",
    "audit",
    "notifications_core",
}


class TenantDBRouter:
    def db_for_read(self, model, **hints):
        institution = hints.get("institution") or current_institution.get()
        if institution and getattr(institution, "isolation_tier", None) == "dedicated_db":
            return institution.db_alias
        return "default"

    db_for_write = db_for_read

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in PLATFORM_APPS:
            return db == "default"
        return True  # tenant apps migrate to every configured alias, including default

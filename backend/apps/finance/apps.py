from django.apps import AppConfig


class FinanceConfig(AppConfig):
    name = "apps.finance"

    def ready(self):
        # Wires the audit-signal receivers on Invoice/Payment/Scholarship —
        # docs/checklist.md's Phase 1 item ("Audit-log signals confirmed
        # firing on every finance write") stayed unchecked until a real
        # finance model existed to wire it to. Imported in ready(), not at
        # module level, so signals.py's own model imports don't run before
        # the app registry is fully populated (same reasoning as every
        # curriculum plugin's registry self-registration in ready()).
        from apps.finance import signals  # noqa: F401

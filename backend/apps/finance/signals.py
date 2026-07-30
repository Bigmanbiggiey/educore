"""Audit-signal wiring for `finance` — docs/architecture.md §6 ("Audit
logging... required for finance and grading changes specifically"),
docs/modules.md's `audit` entry ("wired via signals on sensitive models...
rather than called ad hoc, so logging isn't optional per call site").

`finance` is the first app to actually wire this — `audit.services.log_action`
existed since Phase 1 with no production caller until now
(docs/checklist.md's Phase 1 item stayed unchecked pending a real finance
model). Connected in `FinanceConfig.ready()`, not at import time, so
`finance` never needs `audit` to import it back — same self-registration
direction curriculum plugins use for the engine registry.

`actor` comes from `apps.core.context.current_user`, bound for the request
by `api.viewsets.TenantScopedModelViewSet` — `None` outside a request
(tests constructing rows directly, a future Celery-initiated write), which
`audit.AuditLog.actor` already tolerates (nullable, docs/database.md §2).
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.audit.services import log_action
from apps.core.context import current_institution, current_user
from apps.finance.models import ExpenseRecord, Invoice, Payment, Payroll, Scholarship
from apps.institutions.models import Institution


def _log(action: str, instance) -> None:
    institution = current_institution.get()
    if institution is None:
        # No bound tenant means this write didn't happen through the
        # normal bind_institution-wrapped services.py path (e.g. a raw
        # fixture load) — institution_id is still on the instance itself,
        # so resolve it directly rather than silently skipping the log.
        institution = Institution.objects.filter(id=instance.institution_id).first()
    log_action(
        actor=current_user.get(),
        institution=institution,
        action=action,
        target=instance,
        diff={"id": str(instance.id)},
    )


@receiver(post_save, sender=Invoice)
def _log_invoice_write(sender, instance, created, **kwargs):
    _log("finance.invoice.create" if created else "finance.invoice.update", instance)


@receiver(post_save, sender=Payment)
def _log_payment_write(sender, instance, created, **kwargs):
    _log("finance.payment.create" if created else "finance.payment.update", instance)


@receiver(post_save, sender=Scholarship)
def _log_scholarship_write(sender, instance, created, **kwargs):
    _log("finance.scholarship.create" if created else "finance.scholarship.update", instance)


@receiver(post_save, sender=Payroll)
def _log_payroll_write(sender, instance, created, **kwargs):
    _log("finance.payroll.create" if created else "finance.payroll.update", instance)


@receiver(post_save, sender=ExpenseRecord)
def _log_expense_record_write(sender, instance, created, **kwargs):
    _log("finance.expense_record.create" if created else "finance.expense_record.update", instance)

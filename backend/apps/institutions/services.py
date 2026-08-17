"""Public write interface for `institutions` — docs/modules.md. Other apps
mutate institution state only through these functions, never by touching
apps.institutions.models directly (docs/project-structure.md §3).
"""

import secrets

from django.db import transaction
from django.utils import timezone

from apps.core.signals import institution_provisioned
from apps.institutions.models import Domain, Institution, InstitutionCurriculum

PLATFORM_DOMAIN_SUFFIX = ".educore.africa"


@transaction.atomic
def provision_institution(
    *,
    name: str,
    slug: str,
    curriculum_types: list[str],
    timezone_name: str = "Africa/Nairobi",
    admin_email: str,
    admin_phone: str | None = None,
    actor=None,
) -> Institution:
    """Creates an Institution + its primary subdomain + curriculum row(s),
    then seeds its Institution Administrator, in one transaction —
    docs/multitenancy.md §7's shared_row "fast, self-serve path".

    The admin User/InstitutionMembership/Role + welcome notification are
    NOT created inline here: `institutions` and `accounts` are independent
    Layer 0 siblings under `.importlinter` (neither may import the other),
    and `permissions`/`notifications_core` sit above both, so this
    function can't call into them directly. Instead it fires
    `institution_provisioned` (defined in `apps.core.signals` specifically
    so a sender never needs a forbidden import) after creating the
    Institution/Domain/Curricula, in the same `@transaction.atomic` block —
    Django dispatches signals synchronously and in-process, so
    `apps.permissions`'s receiver (which legally imports both `accounts`
    and `institutions`) still runs, and rolls back, inside this same
    transaction. See `apps.permissions.services.provision_institution_admin`
    for what that receiver does.
    """
    invalid_types = set(curriculum_types) - set(InstitutionCurriculum.CurriculumType.values)
    if invalid_types:
        raise ValueError(f"Unknown curriculum type(s): {sorted(invalid_types)}")

    institution = Institution.objects.create(name=name, slug=slug, timezone=timezone_name)
    Domain.objects.create(
        institution=institution,
        hostname=f"{slug}{PLATFORM_DOMAIN_SUFFIX}",
        domain_type=Domain.DomainType.SUBDOMAIN,
        is_primary=True,
        # Subdomains ride the platform's existing wildcard cert/DNS — no
        # ownership to prove, unlike a custom domain (docs/multitenancy.md §6).
        verified_at=timezone.now(),
    )
    InstitutionCurriculum.objects.bulk_create(
        InstitutionCurriculum(institution=institution, curriculum_type=curriculum_type)
        for curriculum_type in curriculum_types
    )
    institution_provisioned.send(
        sender=provision_institution,
        institution=institution,
        admin_email=admin_email,
        admin_phone=admin_phone,
        actor=actor,
    )
    return institution


def set_isolation_tier(institution: Institution, tier: str, *, db_alias: str = "") -> Institution:
    """Sets an institution's isolation tier directly — for a freshly
    provisioned institution with no tenant data yet (e.g. an enterprise
    customer choosing `dedicated_db` at signup).

    This is NOT the live upgrade path for an institution that already has
    data in its current location; that's `upgrade_isolation_tier`, an
    explicitly-deferred maintenance-window runbook (docs/multitenancy.md
    §7) not built yet.
    """
    if tier not in Institution.IsolationTier.values:
        raise ValueError(f"Unknown isolation tier: {tier!r}")
    if tier == Institution.IsolationTier.DEDICATED_DB and not db_alias:
        raise ValueError("dedicated_db tier requires a db_alias")
    if tier != Institution.IsolationTier.DEDICATED_DB:
        db_alias = ""

    institution.isolation_tier = tier
    institution.db_alias = db_alias
    institution.save(update_fields=["isolation_tier", "db_alias", "updated_at"])
    return institution


def add_custom_domain(institution: Institution, hostname: str) -> Domain:
    """Starts the custom-domain verification flow (docs/multitenancy.md
    §6, steps 1-2): creates the Domain row and a TXT-record token the
    institution admin must publish at their DNS provider before
    `verify_domain` will succeed.
    """
    return Domain.objects.create(
        institution=institution,
        hostname=hostname,
        domain_type=Domain.DomainType.CUSTOM,
        is_primary=False,
        verification_token=secrets.token_hex(16),
    )


def verify_domain(domain: Domain, *, resolved_txt_records: list[str]) -> Domain:
    """Confirms the TXT record was published and marks the domain
    verified (docs/multitenancy.md §6, steps 3-4).

    Takes the already-resolved TXT records as a parameter rather than
    performing the DNS lookup itself, so the actual `dns.resolver` call —
    and its retry/timeout handling — stays in the Celery task that calls
    this, not in this transactional unit of work. Certificate provisioning
    and the Nginx reload that follow a successful verification
    (docs/deployment.md §5) are that same calling task's job, not this
    function's.
    """
    if domain.verified_at is not None:
        return domain
    if domain.verification_token not in resolved_txt_records:
        raise ValueError("TXT record verification token not found")
    domain.verified_at = timezone.now()
    domain.save(update_fields=["verified_at", "updated_at"])
    return domain

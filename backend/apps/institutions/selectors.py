"""Public read interface for `institutions` — docs/modules.md."""

from apps.institutions.models import Domain, Institution


def get_institution_by_domain(host: str) -> Institution | None:
    """Resolves a request's tenant from its Host header. This is the one
    function `TenantMiddleware` calls (docs/multitenancy.md §2) — deliberately
    unscoped, since it IS the mechanism that establishes tenant scope, not
    something that can itself be tenant-filtered.
    """
    domain = (
        Domain.objects.select_related("institution")
        .filter(hostname=host, institution__is_active=True)
        .first()
    )
    return domain.institution if domain else None

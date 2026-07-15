# EduCore — Multi-Tenancy Design

Status: DRAFT — pending approval
Step: 9 of 10

High-level tenancy principles were set in `docs/architecture.md` §5: every
tenant-scoped model carries an institution reference, tenant resolution
happens in middleware, and business logic never knows which isolation tier
is active. This document specifies the actual mechanism — and one
consequential correction to `docs/database.md`'s conventions table that
building all three isolation tiers now requires.

---

## 1. Correction to `docs/database.md`: No Cross-Database Foreign Keys

`docs/database.md` §1 described `institution_id` as an FK. That needs
amending, and it's worth explaining why plainly rather than glossing over it,
since it's a direct, material consequence of the "build all 3 tiers now"
decision.

**The problem:** Django does not support foreign keys across database
connections — this is a hard framework limitation, not a configuration
choice. For a `dedicated_db`-tier institution, that institution's entire
Layer 1/2 dataset lives in its own physical Postgres database, while
`Institution` and `User` (Layer 0, platform identity) always live in the
shared `default` database (§4 explains why). That means `institution_id` on
every tenant-scoped row, and every `user_id`-style reference
(`Student.user`, `StaffProfile.user`, `Payment.recorded_by`,
`AuditLog.actor`, …), crosses a database boundary for dedicated-DB tenants.
A real Postgres FK constraint cannot span that boundary. Full stop.

**The resolution:** `institution_id` and every reference to `accounts.User`
are stored as **plain indexed `UUIDField`s, not Django `ForeignKey`s** —
on every tenant, including `shared_row`-tier ones where a real FK would
technically work fine. Referential integrity for these fields is enforced at
the service layer, not the database layer:
- `institution_id` is only ever set from the server-resolved tenant context
  (never client input, per `docs/api-design.md` §7), so the surface for a
  dangling value is limited to bugs in institution provisioning/deprovisioning
  — not user input, not a wide attack surface.
- Cross-database `User` lookups go through
  `accounts.selectors.get_users_by_ids([...])` (batched, explicit
  `.using('default')`), never an implicit `select_related('user')` join —
  Django can't join across databases in one query regardless, so this makes
  the always-two-queries reality explicit in the code rather than hidden
  behind ORM sugar that would silently break the moment a tenant is on a
  dedicated DB.

**Why apply this to `shared_row` tenants too, not just `dedicated_db` ones:**
if shared-DB tenants got a real FK and dedicated-DB tenants got a plain UUID,
that would mean two different model definitions depending on isolation
tier — directly violating the promise in `docs/architecture.md` that
business logic (which includes model definitions) doesn't change with
isolation tier. Paying this cost uniformly is what keeps "one codebase, three
tiers" true rather than aspirational. Within a single database, `Payment.invoice`,
`Enrollment.student`, and every other Layer 1/2-to-Layer 1/2 reference keep
normal Django FKs with real constraints — this only applies to references
that cross the Layer 0 (`institutions`/`accounts`) boundary, since Layer 0
data is the one thing that always lives in `default` regardless of a
tenant's isolation tier.

---

## 2. Tenant Context: `contextvars`, Not Thread-Locals

`apps/core` owns a module-level `contextvars.ContextVar`:

```python
current_institution: ContextVar[Institution | None] = ContextVar("current_institution", default=None)
```

Thread-locals break under async/Celery because a thread can be reused across
unrelated requests/tasks without the "local" being cleared — a documented
source of tenant-bleed bugs in naive Django multi-tenancy implementations.
`contextvars` are copied safely per async task and per thread by Python
itself, and — critically — are always explicitly `.set()` at the start of a
unit of work and `.reset(token)` in a `finally` block at the end, so nothing
leaks into the next request or task reusing the same worker process.

**`TenantMiddleware`** (request path):
```python
def __call__(self, request):
    host = request.get_host().split(":")[0]
    if host in settings.PLATFORM_HOSTS:          # e.g. admin.educore.africa
        return self.get_response(request)          # no tenant context set
    domain = Domain.objects.select_related("institution").filter(
        hostname=host, institution__is_active=True
    ).first()                                        # unscoped lookup — this IS the mechanism that establishes scope
    if domain is None:
        return HttpResponseNotFound()
    token = current_institution.set(domain.institution)
    request.institution = domain.institution
    try:
        return self.get_response(request)
    finally:
        current_institution.reset(token)
```

**Celery tasks** (no HTTP request, so no middleware): a `@tenant_aware_task`
decorator wraps every task that touches tenant-scoped data, requires an
explicit `institution_id` argument at enqueue time, resolves it, sets the
context at task start, and resets it in a `finally` — the same discipline
as the middleware, applied because Celery reuses worker processes across
unrelated tasks exactly like threads get reused, so a forgotten reset is a
tenant-bleed bug waiting to happen between two consecutive tasks on the same
worker.

---

## 3. Two Layers, Not One: Explicit Params + Auto-Filtering Manager

`docs/modules.md`'s selector examples (`get_current_term(institution)`,
`get_curriculum_engine(institution)`) already establish the primary pattern:
**services/selectors take `institution` as an explicit parameter.** That's
deliberate, not incidental — explicit parameters are what make a selector
callable from a test with zero request/middleware setup, and make the data
dependency visible in the function signature instead of hidden in ambient
state.

The `contextvars`-backed context from §2 is the second, structural layer:
`TenantScopedModel`'s default manager reads `current_institution.get()` and
auto-filters every queryset with it, **failing loudly** (raising
`TenantContextMissing`) if no context is bound, rather than silently
returning an unfiltered or empty queryset:

```python
class TenantQuerySet(models.QuerySet):
    def _scoped(self):
        institution = current_institution.get()
        if institution is None:
            raise TenantContextMissing("No tenant bound — refusing to query a tenant-scoped model without one.")
        return self.filter(institution_id=institution.id)

class TenantManager(models.Manager):
    def get_queryset(self):
        return TenantQuerySet(self.model, using=self._db)._scoped()
```

This is why the two layers coexist rather than one replacing the other:
explicit parameters are what engineers read and call; the auto-filtering
manager is the safety net that makes accidental cross-tenant leakage
structurally hard even when a call site's explicit filtering has a bug —
the same "defense in depth, not one combined check" principle used for
object-level scoping in `docs/permissions.md` §3.

**Escape hatch:** a small number of platform-level call sites (institution
provisioning, System Administrator "act-as" sessions from
`docs/permissions.md` §7, management commands) need cross-tenant queries.
These use an explicitly named alternate manager,
`Model.all_tenants_unsafe`, deliberately ugly and grep-able. `import-linter`
restricts which apps may reference `all_tenants_unsafe` at all (`institutions`,
platform-admin views, and management commands only) — the same CI-enforced
boundary discipline as everything else in this codebase, applied to the one
place tenant isolation is intentionally lifted.

---

## 4. What Always Lives in the Shared `default` Database

Regardless of any institution's isolation tier: `institutions.Institution`,
`institutions.Domain`, `accounts.User`, and the platform-level rows of
`permissions.Role`/`Permission`. This is what makes login, domain resolution,
and cross-institution identity (a user with memberships at two institutions,
`docs/authentication.md` §4) work uniformly — there is exactly one place to
resolve "who is this person" and "which hostname maps to which institution,"
never a per-database copy that could drift.

---

## 5. Isolation Tiers in Practice

### Tier 1 — `shared_row` (default)
All Layer 1/2 data in `default`, scoped by `institution_id` per §1–3. No DB
router involvement — `db_for_read`/`db_for_write` return `default`.

### Tier 2 — `dedicated_db`
Same physical Postgres server (or a separate one), separate database,
reachable via a Django `DATABASES` alias set on `Institution.db_alias`.

```python
class TenantDBRouter:
    def db_for_read(self, model, **hints):
        institution = hints.get("institution") or current_institution.get()
        if institution and institution.isolation_tier == "dedicated_db":
            return institution.db_alias
        return "default"
    db_for_write = db_for_read

    def allow_migrate(self, db, app_label, **hints):
        if app_label in PLATFORM_APPS:          # core, institutions, accounts, permissions, audit, notifications_core
            return db == "default"
        return True                                # tenant apps migrate to every configured alias, including default
```
Provisioning a `dedicated_db` tenant: create the physical database, add its
alias to `DATABASES` (config reload required — see `docs/deployment.md`),
run tenant-app migrations against the new alias only, create the
`Institution`/`Domain` rows in `default` as normal (§4).

### Tier 3 — `dedicated_infra`
A fully separate Docker Compose stack (own Postgres, Redis, MinIO, own
`.env`, own JWT secret) running identical application images. From that
instance's own point of view, its one database *is* `default` — no router
complexity exists inside a dedicated-infra deployment at all, because it has
exactly one tenant and no sibling tenants to route away from. Provisioning
detail is `docs/deployment.md` §6.

**Deferred, explicitly:** centralized cross-instance reporting (e.g. platform-wide
analytics spanning shared-cluster and dedicated-infra tenants) isn't designed
for v1 — a dedicated-infra tenant is operationally standalone, reachable only
through its own admin, not the shared platform's admin panel. A lightweight
metrics-push mechanism to a central platform API is a reasonable future
addition but isn't needed for launch and shouldn't be built speculatively.

---

## 6. Custom Domain Verification Flow

```
1. Institution Admin adds custom domain (e.g. portal.stmary.sc.ke) → Domain row created, verified_at = null
2. System generates a unique TXT record token → Institution Admin adds it at their DNS provider
3. Admin triggers verification → backend does a DNS TXT lookup, confirms token
4. On success: verified_at set, Let's Encrypt certificate requested (docs/deployment.md §5), Nginx reloaded
```
Subdomains (`{slug}.educore.africa`) skip verification entirely — they're
covered by the platform's existing wildcard certificate and DNS is already
under EduCore's control, so there's no ownership to prove.

---

## 7. Institution Provisioning & Tier Upgrades

**Provisioning (shared_row, the fast/self-serve path)** —
`institutions.services.provision_institution(...)` — one DB transaction:
create `Institution` + primary `Domain` (subdomain) + `InstitutionCurriculum`
row(s) + seed the Institution Administrator's `User`/`InstitutionMembership`
+ send welcome notification. Sub-second, no manual steps.

**Isolation tier upgrades (`shared_row` → `dedicated_db` → `dedicated_infra`)**
are explicitly **not** designed as a live, zero-downtime operation for v1 —
that's a substantial engineering effort in its own right (online bulk data
copy with a consistency-verified cutover) and shouldn't gate initial launch.
`services.upgrade_isolation_tier(...)` is a maintenance-window runbook:
Celery-orchestrated bulk copy of the institution's rows into the newly
provisioned destination, integrity verification (row counts, checksums),
DNS/routing cutover, then archival of the old-location data after a
verification window. This is stated plainly as a scoped limitation rather
than implied to be seamless — worth knowing now, before an enterprise
customer is promised same-day tier upgrades.

---

## 8. What This Document Deliberately Defers

- `TenantDBRouter` and `all_tenants_unsafe` full implementation → written
  during `institutions`/`core` app implementation.
- Dedicated-infra provisioning script and its exact runbook steps →
  `docs/deployment.md` (Step 10).

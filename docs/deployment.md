# EduCore — Deployment Design

Status: DRAFT — pending approval
Step: 10 of 10

Closes the design phase. `docs/architecture.md`'s decision log committed to
dedicated-infra provisioning being "a repeatable, scriptable operation, not
a one-off manual process" — §8 here is where that commitment gets a concrete
shape.

---

## 1. Docker Compose Topology

One `docker-compose.yml`, parameterized by `.env`, used identically for the
shared cluster and every dedicated-infra tenant (`docs/multitenancy.md` §5) —
only the `.env` contents differ.

| Service | Image | Notes |
|---|---|---|
| `nginx` | custom, from `docker/nginx/` | reverse proxy, static/media, TLS termination point for origin (see §3) |
| `frontend` | custom, from `docker/frontend/` | Vite build output served as static files — no Node process at runtime |
| `backend` | custom, from `docker/backend/` | gunicorn + Django, `/healthz/` endpoint for readiness |
| `postgres` | `postgres:16` | named volume, one instance serves `default` + any `dedicated_db`-tier tenant databases on the shared cluster |
| `redis` | `redis:7` | cache + Celery broker/result backend |
| `minio` | `minio/minio` | object storage; shared-cluster deployments use one instance with per-institution bucket prefixes, dedicated-infra deployments get their own |
| `celery-worker` | same image as `backend` | `celery -A config worker`, scaled via `--scale celery-worker=N` as load requires |
| `celery-beat` | same image as `backend` | scheduled jobs (fee reminders, nightly rollups, backups §6) — exactly one instance, never scaled |

`backend` and `celery-worker`/`celery-beat` share one image — no separate
build pipeline for worker code, since they're the same codebase running a
different entrypoint command.

---

## 2. Environment Separation

`docker-compose.yml` (base) + `docker-compose.dev.yml` (bind-mounts source
for hot reload, `DEBUG=True`, relaxed CORS) + `docker-compose.prod.yml`
(named volumes only, `DEBUG=False`, gunicorn worker count tuned to host
CPU). No `staging` compose file — staging is a separate `.env` pointed at
`docker-compose.yml` + `docker-compose.prod.yml`, same as production, since
the entire point of staging is to exercise the exact production topology
before it reaches real institutions' data.

---

## 3. Edge: Cloudflare + Nginx

- **Cloudflare mode: Full (strict).** Cloudflare terminates edge TLS for
  visitors and re-encrypts to origin Nginx using a Cloudflare Origin CA
  certificate — never "Flexible" mode, which would leave the Cloudflare→origin
  hop unencrypted and defeat the point of TLS on a system handling student
  and financial data.
- **Subdomains** (`*.educore.africa`): one wildcard certificate covers all
  of them — Cloudflare-issued origin cert, no per-institution certificate
  work at all.
- **Custom domains** (`portal.stmary.sc.ke`): provisioned via **Cloudflare
  for SaaS (custom hostnames)**, not a self-managed `certbot` process per
  tenant. This is a deliberate recommendation over the DIY alternative:
  running Let's Encrypt/certbot ourselves per custom domain means owning
  renewal automation, failure alerting, and rate-limit management for every
  new tenant domain — operational surface that scales linearly with tenant
  count. Cloudflare for SaaS is a paid tier addition, but it turns "add a
  custom domain" into an API call with certificate issuance and renewal
  handled entirely on Cloudflare's side. Given the multi-tenant custom-domain
  requirement is core to the product (not an edge case), paying for this
  now is cheaper than the alternative of building and maintaining
  certificate automation ourselves.
- **Nginx's job**, once TLS is terminated: `Host`-header-based routing to
  `frontend` (static assets, SPA fallback to `index.html`) or `backend`
  (`/api/`, `/admin/`), gzip/brotli, `limit_req` as a coarse first line of
  rate limiting ahead of DRF's own throttles (`docs/api-design.md` §13).

---

## 4. CI/CD & Release Process

GitHub Actions, on every PR: lint (`ruff`, `eslint`), `import-linter`
boundary check (`docs/project-structure.md` §5), backend + frontend test
suites, `docker build` for both images (build failure = CI failure, catches
Dockerfile drift early). On merge to `main`: images tagged with the commit
SHA and pushed to a registry (GitHub Container Registry).

**Deploy (single VPS, no Kubernetes, so this stays deliberately simple):** a
deploy script over SSH runs `docker compose pull && docker compose up -d`
with the new image tag. For near-zero-downtime on the `backend` service
specifically: two `backend` replicas behind Nginx's upstream block, restarted
one at a time with a health-check gate (`/healthz/`) between each — achievable
with plain Docker Compose `--scale` and a short shell script, no orchestrator
needed. `frontend` (static files) and `celery-worker` restarts are simpler:
brief interruption is acceptable for static assets (CDN-cached at Cloudflare
regardless) and Celery tasks are designed to be safely retryable.
**Rollback:** redeploy the previous commit SHA's image tag — always available
in the registry, so rollback is the same script with a different tag, not a
rebuild.

---

## 4a. First-Run Bootstrap: Platform Administrator

A fresh environment (shared cluster or a dedicated-infra tenant that needs
its own break-glass System Administrator) starts with zero `User` rows —
there is no login possible yet, so no HTTP endpoint can create the first
one. Bootstrap it once, manually, via:

```
docker compose exec backend python manage.py bootstrap_platform_admin \
  --email admin@example.com --password '...'
```

(or `PLATFORM_ADMIN_EMAIL`/`PLATFORM_ADMIN_PHONE`/`PLATFORM_ADMIN_PASSWORD`
env vars, supplied via the §5 secrets mechanism, instead of CLI args). The
command refuses to run if a platform-staff user already exists, so it's
safe to leave documented as a step rather than something to remember to
skip on redeploy. It is **not** wired into `entrypoint.sh` — a deliberate
choice: an environment gets exactly one platform admin, created once, by
whoever holds the deploy secrets, not automatically on every container
start.

Once this admin exists, they can log in via `PlatformLoginView`
(`/api/v1/platform/auth/login/`) and provision institutions — each of
which automatically seeds its own Institution Administrator (§8 below no
longer needs a separate manual step for that part).

---

## 5. Secrets Management

Every deployment (shared cluster, each dedicated-infra tenant) has its own
`.env` — database credentials, Redis URL, MinIO keys, JWT `HS256` secret
(`docs/authentication.md` §1), M-Pesa API credentials. Never committed;
`.env.example` documents required keys with placeholder values. Rotation is
a documented runbook (regenerate secret → update `.env` → rolling restart),
not automated for v1 — flagged as a reasonable manual process at current
scale, revisit if the number of dedicated-infra deployments grows large
enough that manual rotation becomes the bottleneck.

---

## 6. Backups & Disaster Recovery

- **Postgres:** nightly `pg_dump` per database (the shared `default` DB, and
  each `dedicated_db`-tier tenant's database separately), via `celery-beat`,
  encrypted and pushed to MinIO under a dedicated `backups` bucket with a
  lifecycle policy retaining 30 daily + 12 monthly snapshots. WAL archiving
  (continuous, point-in-time recovery) is noted as a future upgrade once an
  institution's data volume justifies recovery-point-objectives tighter than
  "up to 24 hours," not built for v1.
- **Dedicated-infra tenants:** same nightly `pg_dump` mechanism, running
  against their own standalone Postgres, pushed to their own MinIO instance
  — backups never leave the tenant's own infrastructure, which is precisely
  what "dedicated infrastructure" is supposed to mean; a central backup
  pipeline reaching into a dedicated-infra tenant's data would quietly
  violate the isolation guarantee that tier exists to provide.
- **MinIO (documents/media):** versioning enabled on buckets holding
  student documents and generated reports — accidental overwrite/delete is
  recoverable without a separate backup job.
- Restore procedure is a documented runbook, tested quarterly against a
  staging restore (a backup nobody has ever restored is not a backup that
  can be trusted).

---

## 7. Monitoring & Observability

Deliberately lightweight for a single-VPS deployment — no self-hosted
ELK/Prometheus stack at launch, since that's meaningful operational overhead
with no user base yet to generate signal worth that cost:
- **Error tracking: Sentry** (hosted, generous free tier) wired into both
  Django and React — highest-value-per-effort addition, since uncaught
  exceptions are the failures that most need a human immediately, and
  Sentry gives stack traces + the `correlation_id` from
  `docs/architecture.md` §6 in one place.
- **Uptime:** external check (e.g. UptimeRobot/Better Uptime) hitting
  `/healthz/` per deployment — catches "the whole VPS is down," which
  internal monitoring can't observe.
- **Logs:** structured JSON to stdout (Docker's default log driver),
  `logrotate`-bounded on-disk retention. A real log-aggregation stack
  (Loki, or similar) is a natural addition once traffic and institution
  count justify it — explicitly deferred, not an oversight.

---

## 8. Dedicated-Infra Tenant Provisioning (the runbook, made concrete)

A single `provision-dedicated-tenant.sh` (Ansible is the natural upgrade if
the number of dedicated-infra tenants grows past what a shell script
comfortably handles — not adopted preemptively) drives:

1. Provision a fresh VPS (cloud provider API or manual — the script assumes
   a bare Ubuntu host with SSH access, doesn't provision the VM itself).
2. Install Docker + Docker Compose.
3. Copy the standard `docker/` directory + `docker-compose.yml` +
   `docker-compose.prod.yml` to the host.
4. Generate a fresh `.env`: new DB credentials, new `HS256` secret, new
   MinIO keys — **never reused from the shared cluster or another tenant**,
   since a shared secret across dedicated-infra tenants would undermine the
   isolation the tier is sold on.
5. `docker compose up -d`, wait for `backend` healthcheck.
6. Run migrations (all apps migrate into this instance's sole `default`
   database — no router complexity here, per `docs/multitenancy.md` §5).
7. Seed platform default data: the 12 system `Role` templates
   (`docs/permissions.md` §2), default `NotificationTemplate`s — both are
   data migrations, applied automatically by step 6.
7a. Bootstrap this tenant's own platform System Administrator (§4a above) —
    only needed if this dedicated-infra tenant runs its own
    `admin.educore.africa`-equivalent panel, rather than being managed from
    the shared cluster's platform host.
8. Create the `Institution` + `Domain` row for this tenant via
   `POST /api/v1/platform/institutions/` (or the System Administrator
   portal) — this automatically seeds the Institution Administrator
   User/InstitutionMembership/role and sends their welcome/set-password
   email, no separate manual account-creation step needed.
9. Point DNS (customer's domain, CNAME'd per §3) and register it with
   Cloudflare for SaaS for certificate issuance.
10. Register the new host with the uptime monitor (§7).

This entire sequence is what makes "dedicated infrastructure without
changing business logic," committed to in `docs/architecture.md`'s decision
log, actually true rather than a slide-deck claim — the same application
image, the same migrations, the same seed data path as the shared cluster,
just aimed at a standalone host.

---

## 9. What This Document Deliberately Defers

- WAL-based point-in-time recovery, full metrics/log-aggregation stack,
  automated secret rotation — all named above as reasonable future upgrades
  once real usage justifies their cost, not built speculatively now.
- VM provisioning automation (Terraform/cloud API) for §8 step 1 — the
  runbook assumes a host already exists; automating host creation itself is
  a separate, smaller addition once the manual step becomes a bottleneck.

---

## Design Phase Complete

This closes all 10 steps: architecture, folder structure, Django apps, React
architecture, database, API, authentication, permissions, multi-tenancy, and
deployment. Per the project's stated process, implementation now proceeds
module by module — each module gets its own pass through: explain feature →
explain database → models → migrations → serializers → services →
permissions → views → URLs → tests → frontend pages → hooks → forms →
documentation → review.

**Recommended first module: `core` + `institutions` + `accounts` +
`permissions`** (Layer 0) — nothing else can be built or tested without
the tenant-scoping mechanism, identity, and RBAC foundation these provide.

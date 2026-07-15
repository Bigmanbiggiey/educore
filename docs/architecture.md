# EduCore — Overall Architecture

Status: DRAFT — pending approval
Step: 1 of 10 (Overall Architecture) in the pre-implementation design process

---

## 1. Architectural Style: Modular Monolith

**Decision:** EduCore is built as a single Django deployment composed of strictly-bounded
Django apps ("modules"), not a microservices constellation.

**Why:**
- Deployment target is one Ubuntu VPS via Docker Compose, no Kubernetes. Microservices
  demand a service mesh, distributed tracing, network-partition handling, and per-service
  CI/CD — costs with no corresponding benefit at this scale.
- A school ERP's modules (Finance, Attendance, Students, Timetable) are highly
  relational and frequently need cross-module transactions (e.g., admitting a student
  touches Students, Finance, and Classes atomically). Distributed transactions across
  microservices are a well-known source of consistency bugs; a single DB transaction
  is not.
- Modular monolith preserves an extraction path: if in future a specific module
  (e.g., Communication/SMS fan-out) needs independent scaling, it can be pulled out
  because module boundaries are already enforced in code, not just convention.

**Rule enforced from day one:** Django apps do not import each other's models directly
across module boundaries except through an explicit `services.py` / `selectors.py`
public interface. No app reaches into another app's ORM internals. This is the
"module boundary discipline" that makes future extraction possible and keeps the
monolith from decaying into a big ball of mud.

---

## 2. System Context

```
                    ┌─────────────────────────────────────────┐
                    │              Cloudflare                 │
                    │   (DNS, TLS proxy, DDoS, caching)        │
                    └───────────────────┬───────────────────────┘
                                         │
                    ┌────────────────────▼────────────────────┐
                    │                  Nginx                   │
                    │   (reverse proxy, static/media, TLS)      │
                    └──────────┬─────────────────┬──────────────┘
                                │                 │
                  ┌─────────────▼──────┐   ┌───────▼─────────────┐
                  │   Frontend (SPA)    │   │   Backend (Django)   │
                  │  React/Vite build,  │   │  DRF API, /api/v1/   │
                  │  served as static   │   │                       │
                  └──────────────────────┘   └───────┬───────────────┘
                                                       │
                    ┌──────────────────────────────────┼───────────────────────┐
                    │                                  │                       │
             ┌───────▼───────┐                 ┌────────▼────────┐     ┌────────▼────────┐
             │  PostgreSQL    │                 │      Redis       │     │      MinIO       │
             │ (system of      │                 │ (cache, broker,  │     │ (documents,      │
             │  record)        │                 │  sessions)       │     │  media, backups) │
             └────────────────┘                 └────────┬────────┘     └──────────────────┘
                                                           │
                                                  ┌─────────▼─────────┐
                                                  │  Celery Worker(s)  │
                                                  │  Celery Beat       │
                                                  │ (SMS/Email/reports,│
                                                  │  scheduled jobs)   │
                                                  └────────────────────┘
```

Institutions reach the platform via:
- Subdomain: `*.educore.africa` → wildcard DNS + wildcard TLS via Let's Encrypt
- Custom domain: `portal.stmary.sc.ke` → CNAME to EduCore, verified + TLS provisioned
  per domain
- Enterprise: dedicated VPS running the same Docker Compose stack, one tenant only

All three cases run identical application code. Only routing/DNS and (optionally)
the DB connection differ.

---

## 3. High-Level Components

| Component | Responsibility |
|---|---|
| **API Gateway layer** (Nginx) | TLS termination, static/media serving, request routing, rate limiting (via `limit_req`), gzip/brotli |
| **Backend (Django + DRF)** | All business logic, all modules, tenant resolution, auth, permissions |
| **Frontend (React SPA)** | Portal shells per role, consumes REST API only — no server-side rendering needed for an internal ERP |
| **PostgreSQL** | System of record. One physical DB for shared-tenant institutions; additional DBs for dedicated-tenant institutions, all reachable from the same backend via DB routing |
| **Redis** | Celery broker/result backend, DRF throttle counters, cache backend (per-tenant key prefixing) |
| **Celery + Beat** | Async jobs: SMS/email dispatch, PDF report card generation, scheduled fee reminders, nightly backups, analytics rollups |
| **MinIO** | S3-compatible object storage for student documents, report PDFs, receipts, backups — never on local disk, so containers stay stateless and horizontally replaceable |

---

## 4. Module Boundaries (Django Apps)

Apps are grouped into four layers. Layers may only depend **downward**.

**Layer 0 — Platform (no institution scope, or defines the scoping mechanism itself)**
`accounts` (auth/users), `institutions` (tenancy root), `permissions` (RBAC),
`audit` (audit logging), `notifications_core` (channel-agnostic dispatch engine)

**Layer 1 — Core Domain (every curriculum needs these)**
`students`, `staff`, `parents`, `classes_streams`, `attendance`, `timetable`,
`finance`, `library`, `inventory`, `transport`, `hostel`, `clinic`, `documents`,
`communication`, `admissions`

**Layer 2 — Curriculum Plugins (pluggable, implement a common contract)**
`curriculum_cbc`, `curriculum_844`, `curriculum_british`, `curriculum_tvet`,
`curriculum_university`

Each implements a shared `AssessmentEngine` / `ReportEngine` interface
(defined in Layer 1 as an abstract base, e.g. `academics.contracts`) so Core Domain
code (report generation, gradebook UI data contracts) never branches on
"if curriculum == CBC". Adding a 6th curriculum in future means implementing the
contract, not touching existing modules — this is the concrete mechanism behind your
requirement "future curricula must be addable without rewriting existing code."

**Layer 3 — Cross-cutting / Presentation**
`analytics`, `reports`, `dashboard`, `api` (DRF routers/versioning glue), `ai_gateway`
(stub interface for future AI plugins — Lesson Plan Generator etc. — isolated behind
one module so AI providers can be swapped without touching domain code)

Dependency rule: Layer 2 depends on Layer 1 and Layer 0. Layer 1 depends only on
Layer 0. Layer 0 depends on nothing else in the system. This is enforced by
`import-linter` (CI-checked) once implementation starts — architecture violations
fail the build, not just code review.

---

## 5. Multi-Tenancy — High-Level Approach

(Full design in `docs/multitenancy.md`, Step 9. Summary here for architectural
completeness.)

- Every Layer 1/2 model carries an `institution` FK (never nullable, indexed).
- A `TenantMiddleware` resolves the institution from `Host` header (subdomain or
  custom domain lookup against a `Domain` table) and binds it to request-local
  context — **not** thread-local globals, to stay safe under async/Celery.
- A `TenantQuerySet`/manager mixin auto-filters every query by the bound tenant.
  Business logic never writes `Model.objects.filter(institution=...)` manually —
  omitting the filter is the #1 cause of cross-tenant data leaks in SaaS systems,
  so the safety has to be structural, not a convention engineers remember.
- Isolation tiers, selected per-institution in the `Institution` model, all served
  by the same code:
  1. **Shared DB, row isolation** (default, cheapest, fastest onboarding)
  2. **Dedicated DB, shared infra** (Django DB routing keyed by tenant — same
     containers, separate Postgres database)
  3. **Dedicated infra** (separate VPS, separate Docker Compose stack, same codebase)

---

## 6. Cross-Cutting Concerns

- **AuthN:** JWT (access + refresh), rotation on refresh, refresh token stored
  httpOnly cookie (not localStorage) to reduce XSS token theft risk.
- **AuthZ:** RBAC with per-institution role assignment (a user can hold different
  roles at different institutions — relevant for multi-school group accounts).
  DRF permission classes compose: `IsAuthenticated + BelongsToInstitution + HasRole`.
- **Audit logging:** model-level, append-only, records actor/institution/action/diff;
  required for finance and grading changes specifically (compliance-sensitive).
- **API versioning:** `/api/v1/...` from day one; breaking changes get `/api/v2/`,
  never in-place breakage.
- **Caching:** Redis, cache keys always prefixed `tenant:{institution_id}:...` to
  prevent cross-tenant cache bleed.
- **Background jobs:** anything sending SMS/email, generating PDFs, or doing bulk
  computation (mean grade rollups, GPA calc) goes through Celery — never inline in
  a request/response cycle.
- **Observability:** structured JSON logging, correlation ID per request (propagated
  into Celery tasks), health-check endpoints for Nginx/uptime monitoring.

---

## 7. Deployment Topology (detail in `docs/deployment.md`, Step 10)

Single `docker-compose.yml` per deployment (shared-cluster or enterprise-dedicated),
services: `frontend`, `backend`, `postgres`, `redis`, `minio`, `celery-worker`,
`celery-beat`, `nginx`. Enterprise/dedicated-infra tenants get their own copy of
this exact stack on their own VPS — same images, different `.env`, which is what
makes "dedicated infrastructure without changing business logic" true in practice,
not just in the pitch.

---

## 8. What This Document Deliberately Defers

- Exact DB schema / ERD → `docs/database.md`
- Exact API contract → `docs/api-design.md`
- Full auth/permission matrix per portal → design step 7–8
- Full multi-tenancy implementation (middleware code, DB router) → `docs/multitenancy.md`
- Deployment scripts, backup strategy, CI/CD → `docs/deployment.md`

---

## Decision Log

- **2026-07-15 — Tenancy scope for initial build:** All 3 isolation tiers
  (shared-DB row isolation, dedicated-DB routing, dedicated-infra tooling) will be
  implemented before first launch, not deferred. Rationale: avoids ever needing to
  migrate a live institution's isolation tier under production pressure, at the
  cost of more upfront engineering time before first revenue. This means
  `docs/multitenancy.md` (Step 9) must fully specify the DB router and the
  dedicated-infra bootstrap process, and `docs/deployment.md` (Step 10) must cover
  provisioning a new dedicated-infra tenant as a repeatable, scriptable operation
  — not a one-off manual process — since it's committed to as a first-class
  capability, not an escape hatch.

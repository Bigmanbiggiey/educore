# EduCore — API Design

Status: DRAFT — pending approval
Step: 6 of 10

This fixes the contract every frontend `features/*/api/` hook and every
backend `views.py` must honor. Per-resource field lists are generated per
module at implementation time; what's fixed here are the conventions that
must be consistent across all 27 apps, because inconsistency here is what
makes an API expensive to consume.

---

## 1. URL & Resource Conventions

- Base path: `/api/v1/{resource}/`, one router per app, aggregated in
  `api/v1/urls.py` (`docs/project-structure.md` §3).
- **Prefer flat collections with filter params over deep nesting.**
  `/api/v1/invoices/?student=<id>` rather than
  `/api/v1/students/<id>/invoices/`. Reserve nesting for sub-resources with
  no independent identity outside their parent (`/api/v1/timetables/<id>/periods/`).
  Rationale: `Invoice` is queried by status, term, and payment-method filters
  far more often than "all invoices for one student" — a flat endpoint
  serves every one of those access patterns with one TanStack Query hook and
  one cache key prefix; a nested-only URL would force the frontend to choose
  one primary access pattern and work around it for the rest.
- **Non-CRUD actions get dedicated RPC-style endpoints**, not an overloaded
  `PATCH` with a magic status field:
  `POST /api/v1/admissions/applications/<id>/convert-to-enrollment/`,
  `POST /api/v1/library/loans/<id>/return/`. These frequently trigger a
  cross-app service call (`docs/modules.md`'s admissions→students chain) and
  deserve their own audited, independently-permissioned endpoint rather than
  being disguised as a field edit.

---

## 2. Versioning

Path-based (`/api/v1/`), not header-based — curlable and debuggable without
custom headers, and it's what DRF's tooling assumes by default. A breaking
change ships as `/api/v2/` running alongside `/v1/` until a published
deprecation window closes (minimum 6 months notice to any external
integrator, e.g. a school's existing SIS). In-place breaking changes to `v1`
are never acceptable once any client depends on it.

---

## 3. Response Shape

**Single resource:** the resource JSON directly — no `{ data: ... }` envelope.
Keeps every TanStack Query hook a one-line `return res.json()`.

**List (paginated):** DRF's standard `PageNumberPagination` shape, used as-is
rather than reinvented:
```json
{ "count": 132, "next": "https://.../students/?page=3", "previous": "...", "results": [ ... ] }
```
Default `page_size=25`, client-overridable via `?page_size=`, capped at 100.
`AuditLog` and other high-volume append-only tables are flagged as future
cursor-pagination candidates if offset pagination ever shows up in slow
query logs — not built now, since it adds complexity with no current
evidence it's needed.

**Field casing:** `snake_case` end-to-end — JSON payloads, DRF serializers,
and the TypeScript types generated from them (§9) all use `snake_case`.
No `djangorestframework-camelcase` transform layer. A camelCase↔snake_case
translation layer is a recurring source of subtle bugs (partial transforms,
missed nested objects) for a cosmetic win; TypeScript doesn't care what case
your keys are in.

---

## 4. Error Contract

Every error response, from every app, has this shape — produced by one
custom DRF exception handler (`api/exception_handlers.py`), never hand-rolled
per view:

```json
{
  "error": {
    "code": "validation_error",
    "message": "One or more fields are invalid.",
    "fields": { "admission_number": ["This field is required."] },
    "correlation_id": "b3f1c2..."
  }
}
```

- `code`: stable, machine-readable (`validation_error`, `permission_denied`,
  `not_found`, `conflict`, `rate_limited`, `server_error`) — frontend
  branches on this, never on parsing `message` text.
- `fields`: present only for validation errors; shape maps directly onto
  React Hook Form's `setError(field, {message})` (`docs/frontend-architecture.md` §4).
- `correlation_id`: echoes the request's correlation ID
  (`docs/architecture.md` §6), logged on the backend too — a user bug report
  traces to one backend log line without guesswork.

---

## 5. HTTP Status Codes

| Status | Meaning | Notes |
|---|---|---|
| 200 / 201 / 204 | success | 201 for creates (with `Location` header), 204 for deletes |
| 400 | validation error | field-level errors in `error.fields` |
| 401 | unauthenticated | missing/expired access token |
| 403 | authenticated, but lacks permission **within their own tenant** | e.g. a Teacher hitting a Finance-only endpoint |
| 404 | not found, **including cross-tenant access attempts** | see below |
| 409 | conflict | e.g. duplicate M-Pesa transaction reference |
| 429 | rate limited | see §8 |
| 500 | server error | generic message only, never a stack trace; `correlation_id` always present |

**Security-critical rule: cross-tenant access returns 404, never 403.**
If a user from Institution A requests an object belonging to Institution B,
the response is 404. Returning 403 would confirm the object *exists* in
another tenant — a tenant-enumeration information leak. This requires no
special-case code: because `TenantScopedModel`'s manager auto-filters every
queryset by the bound tenant (`docs/architecture.md` §5), a cross-tenant
object is simply absent from the queryset — DRF's `get_object_or_404`
produces the right status for free. The only discipline required is that no
view is ever written against `Model.objects` directly, only the tenant-scoped
manager — which is the same rule `docs/project-structure.md` §3 already
enforces for other reasons.

---

## 6. Filtering, Search, Ordering

- **Filtering:** `django-filter` `FilterSet` per resource, with an **explicit
  whitelist** of filterable fields — never blanket/arbitrary field filtering.
  Beyond stability, this is a security boundary: unrestricted filtering
  would let a client discover which fields exist and mine data along axes
  the UI never intended to expose (e.g. filtering staff by salary band).
- **Search:** `?search=` via DRF `SearchFilter` on a curated field list per
  resource (e.g. student name + admission number), not full-text everywhere.
- **Ordering:** `?ordering=field,-field2` via `OrderingFilter`, same
  whitelist discipline as filtering.

---

## 7. Authentication Endpoints

```
POST /api/v1/auth/login/                  { email|phone, password } → { access_token }, sets refresh cookie
POST /api/v1/auth/refresh/                 (reads refresh cookie)    → { access_token }
POST /api/v1/auth/logout/                  blacklists + clears refresh cookie
POST /api/v1/auth/password-reset/request/
POST /api/v1/auth/password-reset/confirm/
GET  /api/v1/auth/me/                      → user + institution memberships + roles
```

All other requests: `Authorization: Bearer <access_token>`. **There is no
`institution_id` parameter anywhere in the API** — tenant is resolved
server-side from the `Host` header by `TenantMiddleware`
(`docs/architecture.md` §5), never accepted as client input. This closes off
an entire class of "pass a different institution_id in the request body and
see what happens" attacks before it can exist, and matches the frontend
contract in `docs/frontend-architecture.md` §3 (query keys carry no tenant
segment because the API never needs one).

---

## 8. Curriculum-Aware Endpoints

Rather than forcing the frontend to know which of five URL sets to call
based on an institution's curriculum, curriculum-agnostic endpoints are
exposed wherever the underlying operation is genuinely shared:

```
GET  /api/v1/academics/subjects/
POST /api/v1/academics/assessments/
GET  /api/v1/academics/report-cards/{student_id}/{term_id}/
```

These route through `academics.selectors.get_curriculum_engine(institution)`
server-side (`docs/modules.md`); curriculum-specific fields ride in a
`details` sub-object validated by whichever curriculum's serializer is
selected at runtime. This means `features/academics` on the frontend talks
to one endpoint set, not five — the API-layer mirror of the backend
inversion that already makes curricula pluggable.

Operations with no cross-curriculum equivalent (CBC PCI management, TVET
Industrial Attachment tracking, University Dissertation workflow) get their
own dedicated endpoints under `/api/v1/curriculum-{x}/...` — unifying those
would mean inventing a fake shared abstraction with no real second user,
which is worse than just having five small endpoints.

---

## 9. Generated Types, Not Hand-Written Ones

`drf-spectacular` generates the OpenAPI 3 schema directly from serializers/
views (served at `/api/v1/schema/`, human-readable docs at `/api/docs/` via
Swagger/Redoc — also the integration point for a school's existing SIS in
future). Every serializer field requires `help_text`, enforced by a CI lint
step, so the generated docs stay useful rather than a list of bare field
names.

The frontend runs `openapi-typescript` against that schema to generate
`shared/lib/api-types.ts` — response types are **generated, never
hand-written interfaces**. Hand-written interfaces drift silently from the
real API shape; generated ones fail the build the moment backend and
frontend disagree. This is distinct from the Zod schemas in
`docs/frontend-architecture.md` §4, which validate *form input* for UX —
generated OpenAPI types describe what the server actually returns.

---

## 10. File Uploads — Direct to MinIO

```
POST /api/v1/documents/upload-url/   { filename, content_type, category }
  → { upload_url (presigned PUT), document_id, fields }
[client PUTs the file bytes directly to MinIO, not through Django]
POST /api/v1/documents/{id}/confirm/  → marks uploaded, enqueues virus-scan/processing task
```

Keeps large file bytes off Django/gunicorn workers entirely — a worker
streaming a 20MB report card PDF is a worker not serving API requests. The
same presigned-URL pattern applies in reverse for downloads: `reports`
writes generated PDFs straight to MinIO and returns a presigned GET URL,
never proxying the bytes through the API.

---

## 11. Idempotency & Webhooks

- **M-Pesa callback:** `POST /api/v1/webhooks/mpesa/callback/` — verified via
  M-Pesa's source-IP allowlist and payload signature, not JWT (external
  caller). M-Pesa retries callbacks on timeout, so `Payment` records are
  **upserted keyed on M-Pesa's `TransactionID`** (unique constraint): a
  duplicate callback is a no-op 200, never a duplicate payment. Getting this
  wrong is a direct financial-integrity bug, not a cosmetic one.
- **Client-initiated finance writes** (manual cash/bank entry) accept an
  optional `Idempotency-Key` header; the response for a given key is cached
  and replayed rather than the operation re-executing. Cheap insurance
  against double-submit-on-flaky-network, applied precisely where
  duplication is costliest.

---

## 12. Bulk Operations

Dedicated bulk endpoints where the use case is genuinely batch (marking a
whole class's attendance, importing students from an admissions CSV) —
`POST /api/v1/attendance/bulk-mark/` — rather than the client looping N
single-resource POSTs. One DB transaction, one audit log entry describing
the batch, and no N-times-the-latency round trip.

---

## 13. Rate Limiting

Redis-backed DRF throttles:
- Anonymous/login endpoints: aggressive (e.g. 5/min/IP) — brute-force
  protection on the one endpoint that must accept unauthenticated traffic.
- Authenticated: generous per-user ceiling (e.g. 600/min) — a safety net
  against a runaway frontend retry loop, not a real limit under normal use.
- Webhook endpoints: no per-caller throttle; the source-IP allowlist is the
  actual control, since a legitimate M-Pesa retry burst shouldn't be throttled.

---

## 14. Explicitly Not Adopted: GraphQL

REST fits this API's actual shape — mostly CRUD plus a small set of RPC-style
actions, consumed by one first-party frontend (plus, later, one integration
surface for third-party SIS). GraphQL would add a second query paradigm and
a resolver layer to maintain without solving a problem EduCore has — there's
no deeply-nested, client-driven query flexibility requirement here that REST
+ well-chosen list endpoints doesn't already cover.

---

## 15. What This Document Deliberately Defers

- Full serializer field lists per resource → generated per module at
  implementation time, per `docs/database.md`'s equivalent scoping note.
- Exact throttle rates, tuned once real traffic patterns exist.
- Third-party SIS integration authentication (API keys / OAuth2 client
  credentials) — noted as a future need above, not designed now since no
  concrete integration partner exists yet.

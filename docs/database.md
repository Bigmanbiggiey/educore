# EduCore — Database Design

Status: DRAFT — pending approval
Step: 5 of 10

Scope note: this document fixes **entities, relationships, cardinality, and
constraints** — the decisions that are expensive to change after data exists.
Exact field-by-field migrations for each app are generated during that app's
own implementation pass (per the per-module process in the project brief:
"explain database → generate models → generate migrations"), not all upfront
here. Layer 0 is the exception — it's specified to full field level below
because every other table depends on it and it will not change shape later.

---

## 1. Conventions (apply to every table unless stated otherwise)

| Convention | Decision | Why |
|---|---|---|
| Primary key | **UUIDv7** (time-ordered UUID, not UUIDv4), via `django-uuidv7` or a small custom default | Random UUIDv4 PKs cause B-tree index fragmentation and poor insert locality in Postgres at scale — a well-known footgun. UUIDv7 keeps the "unguessable, mergeable across dedicated tenant DBs" benefits of UUID while sorting mostly-sequentially, so index performance stays close to a bigint PK. This directly matters for the dedicated-DB tenancy tier: UUID PKs mean no collision risk if institutions are ever consolidated or migrated between isolation tiers. |
| Timestamps | `created_at`, `updated_at` (auto) on every table, via `TimeStampedModel` | Audit and debugging baseline; not optional per-model. |
| Soft delete | `deleted_at` (nullable) via `SoftDeleteModel`, **only** on tables where a wrong hard-delete is costly or where historical reference matters (Student, Staff, Invoice, Payment, Enrollment, Document). Pure lookup/config tables (e.g. `Permission`, `NotificationTemplate`) hard-delete. | Soft-deleting everything bloats every query with a filter and every unique constraint with a partial-index workaround for no benefit on tables with no downstream financial/legal/historical reason to keep tombstones. |
| Tenant scoping | `institution_id`, **not null**, indexed, on every Layer 1/2 table, via `TenantScopedModel` — stored as a plain `UUIDField`, **not a Django `ForeignKey`** (see `docs/multitenancy.md` §1 for why: Django cannot enforce FK constraints across the database boundary that `dedicated_db`-tier tenants introduce, so this is applied uniformly to keep one model definition working under every isolation tier) | Structural tenant isolation — see `docs/architecture.md` §5. `Institution` and `Domain` themselves are the only tables without an `institution_id` (they define the tenant). `User`/`accounts.User` is also exempt — identity is platform-global, see §2, and any reference to it from a tenant-scoped model is likewise a plain UUID, not an FK, for the same cross-database reason. |
| Naming | `snake_case` tables/columns, singular model name → Django's default plural table name, FK columns suffixed `_id` implicitly by Django | Standard Django convention, no reason to deviate. |
| Money | `DecimalField(max_digits=12, decimal_places=2)`, never float | Standard for financial correctness — never negotiable in a finance module. |
| Enums | Postgres-backed `TextChoices`, not free-text | Keeps invalid states unrepresentable at the DB layer, not just validated in a serializer. |

---

## 2. Layer 0 — Platform Schema (full detail)

### `Institution`
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| name | varchar | |
| slug | varchar, unique | used to construct default subdomain: `{slug}.educore.africa` |
| isolation_tier | enum(`shared_row`, `dedicated_db`, `dedicated_infra`) | drives DB router, `docs/multitenancy.md` |
| db_alias | varchar, nullable | Django DB alias when `isolation_tier = dedicated_db` |
| timezone | varchar | default `Africa/Nairobi`, overridable (global-ready) |
| logo_url, primary_color, favicon_url | varchar | branding, consumed by frontend theming (`docs/frontend-architecture.md` §6) |
| is_active | bool | tenant-level kill switch (suspension for non-payment etc.) |
| created_at, updated_at | timestamp | |

### `InstitutionCurriculum` (M2M through: Institution ↔ curriculum type)
A **deliberate departure** from a single `curriculum_type` field on `Institution`:
Kenyan institutions frequently run more than one curriculum concurrently — a
primary school mid-transition teaching CBC in lower grades and 8-4-4 in upper
grades, or a college offering both TVET and University programmes. Modeling
this as M2M from day one avoids a painful migration later; modeling it as a
single enum would be the convenient-but-wrong shortcut.
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| institution | FK → Institution | |
| curriculum_type | enum(`cbc`, `844`, `british`, `tvet`, `university`) | |
| is_active | bool | |

`academics.selectors.get_curriculum_engine(institution, curriculum_type=None)`
takes an explicit curriculum type when an institution runs more than one, and
falls back to the sole entry when there's only one — this is why the resolver
signature in `docs/modules.md` takes `institution`, not a hardcoded
`institution.curriculum_type`.

### `Domain`
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| institution | FK → Institution | |
| hostname | varchar, unique | `stmary.educore.africa` or `portal.stmary.sc.ke` |
| domain_type | enum(`subdomain`, `custom`) | |
| is_primary | bool | one primary per institution (partial unique index) |
| verified_at | timestamp, nullable | custom domains require DNS TXT verification before activation |

### `User` (accounts) — platform-global, intentionally has no `institution_id`
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| email | varchar, unique, nullable | login identifier option 1 |
| phone | varchar, unique, nullable | login identifier option 2 (E.164) |
| password_hash | varchar | Django's standard hasher |
| is_platform_staff | bool | System Administrator portal access — platform-level, not institution-scoped |
| is_active | bool | |
| last_login, date_joined | timestamp | |

Check constraint: `email IS NOT NULL OR phone IS NOT NULL`.

### `Role`
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| institution | FK → Institution, **nullable** | null = global template role (Teacher, Principal, Parent…) shared across all institutions; set = institution-defined custom role |
| name | varchar | |
| is_system | bool | true for the ~12 portal-default roles seeded at platform install; prevents accidental deletion |

Global template roles avoid every institution having to redefine "Teacher"
from scratch, while the nullable FK still allows an institution to define a
bespoke role (e.g. "Exams Coordinator") without a schema change.

### `Permission`
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| code | varchar, unique | dotted namespace: `{app}.{resource}.{action}`, e.g. `finance.invoice.create` — mirrors the `services.py` function it gates |
| description | varchar | |

### `RolePermission` (M2M through: Role ↔ Permission)

### `InstitutionMembership`
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| user | FK → User | |
| institution | FK → Institution | |
| status | enum(`active`, `suspended`) | |
| is_default | bool | which membership a multi-institution user lands in post-login |
| unique_together | (user, institution) | one membership row per user per institution — roles are M2M off this row, not off the (user, institution) pair directly, so… |

### `MembershipRole` (M2M through: InstitutionMembership ↔ Role)
Allows a person to hold multiple roles at one institution (a Deputy Principal
who also teaches is a real, common case) without denormalizing role lists
onto `InstitutionMembership` itself.

### `AuditLog` (append-only — no `updated_at`, no soft delete, rows are never mutated)
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| institution | FK → Institution, nullable | null for platform-level actions (e.g. System Admin provisioning a tenant) |
| actor | FK → User, nullable | null for system/Celery-initiated actions |
| action | varchar | e.g. `finance.payment.create` |
| target_content_type, target_object_id | generic FK | |
| diff | JSONB | before/after snapshot |
| ip_address | inet | |
| created_at | timestamp | |

### `NotificationTemplate`
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| institution | FK → Institution, nullable | null = platform default, overridable per institution |
| key | varchar | e.g. `fee_reminder` |
| channel | enum(`sms`, `email`, `push`) | |
| subject_template, body_template | text | |

### `NotificationLog`
| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| institution | FK → Institution | |
| recipient_user | FK → User, nullable | nullable to support sending to a raw guardian phone number not yet on the platform |
| recipient_address | varchar | phone/email actually used |
| channel, template_key | varchar | |
| status | enum(`queued`, `sent`, `delivered`, `failed`) | |
| provider_response | JSONB | |
| created_at | timestamp | |

---

## 3. Layer 1 — Core Domain (entity + relationship level)

### The temporal backbone

Nearly every Layer 1/2 table answers "as of when" by referencing `Term`, not
a raw date range — this is the single most load-bearing relationship in the
schema, so it's called out before the rest:

```
AcademicYear (institution, year_label, start_date, end_date)
  └─< Term (academic_year, name, start_date, end_date, is_current)
        ├─< ClassGrade (institution, term, name, curriculum_type)
        │     └─< Stream (class_grade, name, capacity)
        ├─< Enrollment (student, class_grade, stream, term)
        ├─< AttendanceRecord (student_or_staff, term, date, status)
        ├─< Invoice (student, term, ...)
        └─< [every curriculum plugin's assessment tables key off Term]
```

`classes_streams.selectors.get_current_term(institution)` is the single
function nearly every other app calls rather than each computing "current
term" from dates independently — one source of truth for "what term is it,"
important because term boundaries are administratively set (can be adjusted
for a public holiday extension etc.), not purely calendar math.

### Students, Staff, Parents

```
Student (institution, user[nullable — young students may have no login],
         admission_number[unique per institution], date_of_birth, ...)
  ├─< Enrollment (student, class_grade, stream, term, status)
  └─< GuardianRelationship (student, guardian_user, relationship_type,
                              is_primary_contact)

StaffProfile (institution, user[1:1], employee_number, department,
              employment_type, hire_date)

ParentProfile (institution, user[1:1], preferred_language,
               notification_preferences)
```

`GuardianRelationship` lives in `students`, not `parents` — a guardian may
not have a `ParentProfile`/portal account at all (e.g. an emergency contact),
so the relationship must not depend on the profile existing.

### Finance (the highest-scrutiny module — every write audited)

```
FeeStructure (institution, class_grade, term, line_items[JSONB or
              FeeStructureLineItem child table], total_amount)
Invoice (institution, student, term, fee_structure, amount_due, status)
  ├─< InstallmentPlan (invoice, num_installments, schedule)
  └─< Payment (invoice, amount, method[mpesa|cash|bank], reference,
               paid_at, recorded_by)
        └─< Receipt (payment, receipt_number[unique per institution], pdf_document)
Scholarship (institution, student, term, amount_or_percent, funded_by)
Payroll (institution, staff, period, gross, deductions[JSONB], net, paid_at)
ExpenseRecord (institution, category, amount, incurred_at, approved_by)
```

`Payment.recorded_by` and every mutation on this subtree fire `audit.services.log_action`
via signals — not optional, per `docs/modules.md`'s `audit` app design.

### Attendance, Timetable

```
AttendanceRecord (institution, term, date, subject_type[student|staff],
                   target_id, status[present|absent|late|excused])
  — unique_together (term, date, subject_type, target_id)

Timetable (institution, term, class_grade)
  └─< Period (timetable, day_of_week, start_time, end_time)
        └─< SubjectSlotAssignment (period, subject, staff, room)
              — clash-detection enforced in services.py, not just a DB constraint,
                because "clash" spans multiple rows (same staff, overlapping time)
```

### Library, Inventory, Transport, Hostel, Clinic
(entity list — relationships are straightforward FK chains, full field detail
at implementation time)

```
Book → Copy (1:many) → Loan (copy, borrower[Student|Staff via generic FK], due_date) → Fine
Asset, StockItem → StockMovement (in/out, quantity, reason)
Vehicle → Route → Stop; TransportAssignment (student, route, stop)
Hostel → Room → BedAllocation (room, student, term)
HealthRecord (student, allergies, conditions) → ClinicVisit (student, date, notes, treated_by)
```

### Documents, Communication, Admissions

```
Document (institution, category, minio_object_key, content_type_target[generic FK],
          uploaded_by, is_confidential)
Announcement (institution, audience[roles/classes], title, body, published_at)
MessageThread (institution, participants[M2M User]) → Message (thread, sender, body, sent_at)
Application (institution, applicant_details[JSONB or child table], stage, term_applying_for)
  └─< Offer (application, offered_at, accepted_at) → on accept: Enrollment created
```

### `academics` (contracts — no curriculum-specific data, but does own shared tables)

```
GradingScale (institution, curriculum_type, levels[JSONB: label, min, max])
SubjectCatalog (institution, curriculum_type, name, code)
  — the generic "subject" concept curriculum plugins specialize via FK,
    e.g. curriculum_844.CAT references SubjectCatalog, not a separate
    subject list per curriculum plugin
```

---

## 4. Layer 2 — Curriculum Plugins (entity level)

Every table below carries `institution` + a FK chain back to `Student` and
`Term`. None of these tables are ever queried directly by Layer 1/3 code —
always through `academics.selectors.get_curriculum_engine(...)`
(`docs/modules.md`).

**CBC**
```
LearningArea (curriculum-specific subject equivalent)
Competency (learning_area, strand, sub_strand)
CoreValue, PCI (Pertinent and Contemporary Issue)
Project (student, competency, term, description)
ContinuousAssessment (student, competency, term, performance_level[4-tier], evidence_notes)
```

**8-4-4**
```
Subject (→ SubjectCatalog)
CAT, Midterm, EndTerm, Mock (student, subject, term, score, max_score, exam_type)
MeanGradeSnapshot (student, term, mean_score, mean_grade, rank_in_class, rank_in_stream)
   — precomputed by a Celery task after results entry closes, not computed live per request
```

**British**
```
EYFSStage, KeyStage, YearGroup (curriculum-specific class-grade equivalents, map to ClassGrade)
Subject (→ SubjectCatalog, IGCSE/A-Level flagged)
Coursework (student, subject, term, component, score)
PredictedGrade (student, subject, academic_year, predicted_grade, set_by)
```

**TVET**
```
TVETDepartment, Course (department, course_code)
CompetencyUnit (course, unit_code, credit_hours)
IndustrialAttachment (student, host_organization, start_date, end_date, supervisor_report)
WorkshopAssessment, PracticalExam (student, competency_unit, term, score, assessor)
Certificate (student, course, issued_at, certificate_number)
```

**University**
```
Faculty → School → Department → Programme (programme_code, degree_level)
Unit (programme, unit_code, credit_hours, semester_offered)
Semester (academic_year equivalent for university calendar)
CourseRegistration (student, unit, semester, status)
Assignment, CAT, FinalExam (student, unit, semester, score, max_score)
GPASnapshot (student, semester, gpa, cgpa)  — precomputed, same rationale as MeanGradeSnapshot
Dissertation (student, supervisor, title, status)
Graduation (student, programme, conferred_at, classification)
```

---

## 5. Indexing Strategy

- Every `institution_id` FK is indexed — it's in nearly every `WHERE` clause
  by construction (`TenantScopedModel`'s auto-filtering manager).
- Composite indexes on `(institution_id, <hot filter column>)` for the
  highest-traffic lookups: `(institution_id, term_id)` on assessment/finance
  tables, `(institution_id, admission_number)` on `Student`.
- Partial indexes for soft-delete tables: unique constraints (e.g.
  `admission_number` unique per institution) are defined as
  `UNIQUE (institution_id, admission_number) WHERE deleted_at IS NULL`, so a
  re-admitted student after a soft-deleted record doesn't collide.
- No indexes added speculatively beyond the above at design time — additional
  indexes get added per observed query pattern once each module has real
  traffic (`EXPLAIN ANALYZE`-driven, not guessed upfront).

---

## 6. Migration Dependency Order

Django migrations must apply in dependency order matching the layer graph
(`docs/project-structure.md` §5): `core` → `institutions` → `accounts` →
`permissions` → `audit`/`notifications_core` → Layer 1 apps (any order among
themselves, they don't depend on each other) → `academics` → Layer 2
curriculum apps → Layer 3. Django's migration graph resolves this
automatically from FK dependencies, but new apps should be added to
`INSTALLED_APPS` in this order for readability and to catch accidental
reverse-dependencies early (an app that won't migrate cleanly near the top
of the list is a boundary violation surfacing itself).

---

## 7. What This Document Deliberately Defers

- Exact migration files / full field lists for Layer 1/2 tables beyond what's
  shown → generated per module during implementation.
- DB router implementation for `dedicated_db` tier, and dedicated-infra
  provisioning → `docs/multitenancy.md` (Step 9).
- Query-level API contract (what a list endpoint returns, filtering/pagination
  params) → `docs/api-design.md` (Step 6).

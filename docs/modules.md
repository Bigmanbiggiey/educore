# EduCore — Django App Design

Status: DRAFT — pending approval
Step: 3 of 10

Each app below is a Django app under `backend/apps/`. For each: purpose, key
concepts it owns, its public interface (what `services.py`/`selectors.py` expose
to other apps), and its dependencies. Dependencies must only point at equal or
lower layers (see `docs/project-structure.md` §5 — CI-enforced).

Full field-level schema is Step 5 (`docs/database.md`). This step fixes
**ownership boundaries**, which is the harder thing to change later.

---

## Layer 0 — Platform

### `core`
Shared kernel, not a business module. No app-specific business logic.
- **Provides:** `TimeStampedModel`, `SoftDeleteModel`, `TenantScopedModel` (UUID PK
  + `institution` FK + tenant-filtering manager, see `docs/multitenancy.md`),
  base DRF pagination/exception classes, correlation-ID middleware base.
- **Depends on:** nothing.

### `institutions`
The tenancy root — every other tenant-scoped app's FK ultimately points here.
- **Owns:** `Institution` (name, curriculum type(s) offered, branding, isolation
  tier), `Domain` (subdomain/custom-domain → institution mapping, verification
  status), `AcademicCalendarSettings`.
- **Exposes:** `selectors.get_institution_by_domain(host)`,
  `services.provision_institution(...)`, `services.set_isolation_tier(...)`.
- **Depends on:** `core`.

### `accounts`
Identity only — not role/permission, not institution membership.
- **Owns:** custom `User` (email/phone login, no username), password reset,
  MFA hook (future).
- **Why identity is separate from membership:** a user (e.g. a parent with two
  kids at different schools, or a teacher who consults for a second institution)
  can belong to multiple institutions with different roles at each — that's a
  many-to-many concern, not an attribute of the user.
- **Exposes:** `services.register_user(...)`, `selectors.get_user_by_email(...)`.
- **Depends on:** `core`.

### `permissions`
RBAC, and the User↔Institution↔Role link accounts deliberately doesn't own.
- **Owns:** `Role`, `Permission`, `InstitutionMembership` (User + Institution +
  Role[s] — the join model that makes "different role per institution" possible).
- **Exposes:** `selectors.get_user_roles(user, institution)`,
  `services.assign_role(...)`, a library of reusable DRF permission classes
  (`IsInstitutionMember`, `HasRole(...)`) other apps compose in their `views.py`.
- **Depends on:** `core`, `accounts`, `institutions`.

### `audit`
- **Owns:** append-only `AuditLog` (actor, institution, action, target
  content-type/object-id, before/after diff as JSON, timestamp, IP).
- **Exposes:** `services.log_action(actor, institution, action, target, diff)`,
  wired via signals on sensitive models (finance transactions, grade changes,
  role assignments) rather than called ad hoc — so logging isn't optional per
  call site.
- **Depends on:** `core`, `institutions`, `accounts`.

### `notifications_core`
Channel-agnostic dispatch engine. Nothing here knows about "fee reminder" or
"exam results" — that's the `communication` app's job (Layer 1).
- **Owns:** `NotificationTemplate`, `NotificationLog`, pluggable channel backends
  (SMS via e.g. Africa's Talking, Email via SMTP/SES, Push).
- **Exposes:** `services.send(institution, recipient, template_key, context, channel)`
  — always enqueues via Celery (`tasks.py`), never sends synchronously in a request.
- **Depends on:** `core`, `institutions`.

---

## Layer 1 — Core Domain

All models here use `TenantScopedModel`. All apps expose `services.py` (writes)
and `selectors.py` (reads); the table below lists only what's distinctive.

| App | Owns | Notable interface |
|---|---|---|
| `students` | `Student`, `Enrollment` (student↔class↔year), `GuardianRelationship` | `services.enroll_student(...)`, `selectors.get_active_roster(class_id)` |
| `staff` | `StaffProfile` (1:1 User), employment record, department assignment | `selectors.get_teachers_for_subject(...)` |
| `parents` | `ParentProfile` (1:1 User), portal preferences | reads guardian links from `students`, doesn't duplicate them |
| `classes_streams` | `AcademicYear`, `Term`, `ClassGrade`, `Stream`, `ClassTeacherAssignment` | `selectors.get_current_term(institution)` — heavily depended on by almost everything else |
| `attendance` | `AttendanceRecord` (student/staff), attendance policy config | `services.mark_attendance(...)`, `selectors.get_attendance_rate(...)` |
| `timetable` | `Timetable`, `Period`, `SubjectSlotAssignment` | `services.assign_slot(...)` runs clash-detection before committing |
| `finance` | `FeeStructure`, `Invoice`, `Payment` (M-Pesa/Cash/Bank), `Receipt`, `InstallmentPlan`, `Scholarship`, `Payroll`, `ExpenseRecord` | `services.record_payment(...)`, `selectors.get_balance(student)` — audited via `audit` signals |
| `library` | `Book`, `Copy`, `Loan`, `Reservation`, `Fine` | `services.checkout(...)`, `services.return_copy(...)` |
| `inventory` | `Asset`, `StockItem`, `StockMovement`, `Supplier` | `services.record_movement(...)` |
| `transport` | `Vehicle`, `Route`, `Stop`, `TransportAssignment` | `selectors.get_route_manifest(...)` |
| `hostel` | `Hostel`, `Room`, `BedAllocation` | `services.allocate_bed(...)` |
| `clinic` | `HealthRecord`, `ClinicVisit`, `Medication` | access-restricted selectors (nurse role only — enforced via `permissions`) |
| `documents` | `Document` (metadata + MinIO object key), `DocumentCategory`, generic-FK attach point | `services.attach(...)`, `selectors.get_documents_for(target)` — used by `reports` to store generated PDFs |
| `communication` | `Announcement`, `Circular`, `MessageThread` | `services.publish_announcement(...)` calls `notifications_core.services.send(...)` per recipient |
| `admissions` | `Application`, `ApplicationStage`, `Offer` | `services.convert_to_enrollment(application)` calls `students.services.enroll_student(...)` on acceptance — the one sanctioned cross-app write chain |

### `academics` (Layer 1 — the curriculum contract)
This is the mechanism behind "future curricula must be addable without rewriting
existing code," so it's called out separately from the table above.
- **Owns:** abstract contracts only, no curriculum-specific models:
  - `contracts.AssessmentEngine` (ABC: `record_assessment()`, `compute_result()`)
  - `contracts.ReportEngine` (ABC: `generate_report_data(student, term)`)
  - `GradingScale` abstraction, generic `Subject`/`LearningArea` base concept
    curriculum apps specialize.
- **Exposes:** `selectors.get_curriculum_engine(institution)` — resolves to the
  concrete `curriculum_*` implementation based on `institution.curriculum_type`.
  This is the **only** place in Layer 1/3 code that ever needs to know which
  curriculum is active; `reports`, `dashboard`, gradebook UI all call through
  this resolver instead of branching on curriculum type themselves.
- **Depends on:** `core`, `institutions`, `students`, `classes_streams`, `staff`.

---

## Layer 2 — Curriculum Plugins

Each app below implements `academics.contracts.AssessmentEngine` and
`ReportEngine`. **Nothing in Layer 1 or Layer 3 imports from these apps directly**
— they're only ever reached through `academics.selectors.get_curriculum_engine()`.
That inversion is what lets a 6th curriculum be added as a pure addition later.

| App | Owns |
|---|---|
| `curriculum_cbc` | `LearningArea`, `Competency`, `CoreValue`, `PCI`, `Project`, `ContinuousAssessment` record, CBC `PerformanceLevel` (4-tier) |
| `curriculum_844` | `Subject`, `CAT`, `Midterm`, `EndTerm`, `Mock`, ranking/mean-grade computation, KCPE/KCSE result import |
| `curriculum_british` | `EYFSStage`, `KeyStage`, `YearGroup`, IGCSE/A-Level `Subject`, `Coursework`, `PredictedGrade` |
| `curriculum_tvet` | `TVETDepartment`, `Course`, `CompetencyUnit`, `IndustrialAttachment`, `WorkshopAssessment`, `PracticalExam`, `Certificate` |
| `curriculum_university` | `Faculty`, `School`, `Department`, `Programme`, `Unit`, `Semester`, `CourseRegistration`, `Assignment`, `CAT`, `FinalExam`, GPA/CGPA computation, `Dissertation`, `Graduation` |

**Depends on:** `core`, `institutions`, `academics`, `students`, `classes_streams`,
`staff`. Never depended on *by* Layer 1 apps.

---

## Layer 3 — Cross-Cutting / Presentation

### `analytics`
Celery-driven rollups (attendance rates, fee collection %, mean grade trends) —
precomputed, not calculated on every dashboard request.
- **Depends on:** reads via selectors across Layer 1/2 apps. Never writes to them.

### `reports`
Orchestrates report generation (PDF, via WeasyPrint or similar): pulls student
data, calls `academics.selectors.get_curriculum_engine(institution).generate_report_data(...)`,
pulls finance balance, renders, stores the result via `documents.services.attach(...)`.
- **Depends on:** `academics`, `finance`, `attendance`, `documents`.

### `dashboard`
A facade over selectors from many apps, tailored per portal — e.g. the Principal
dashboard aggregates enrollment, attendance, and finance selectors into one
response shape the frontend `portals/principal` consumes. Read-only, no models
of its own beyond cached aggregate snapshots.

### `ai_gateway`
Stub for now — defines `AIProvider` ABC (`generate_lesson_plan`,
`generate_exam`, `predict_performance`, `generate_report_comment`, `chat`) and a
settings-driven provider toggle. No concrete implementation ships in v1; this
exists so that when an AI module is built, it plugs into one seam instead of
touching `curriculum_*` or `reports` directly.

### `api`
Not a Django "app" with models — the DRF routing/versioning glue.
`api/v1/urls.py` aggregates every app's router under `/api/v1/`. Detailed in
`docs/api-design.md` (Step 6).

---

## Why this many apps

27 apps is a lot, and that's intentional, not accidental sprawl: Django's app
boundary is the cheapest enforceable boundary the framework gives us (separate
`services.py`/`selectors.py`, checkable by `import-linter`, independently
testable). Collapsing e.g. `library` and `inventory` into one "assets" app would
save a directory but blur two domains that don't share a lifecycle — a book loan
and a laptop stock movement have nothing in common. The cost of "many small
apps" is navigation overhead, which an IDE solves; the cost of "few large apps"
is boundary erosion, which nothing solves after the fact.

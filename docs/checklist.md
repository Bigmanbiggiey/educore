# Implementation Checklist

Tracks execution against `docs/roadmap.md`, phase by phase. Where a phase
touches Django apps, the build order matches the dependency order fixed in
`docs/modules.md` (Layer 0 → 1 → 2 → 3) — don't start an app before the ones
above it in its list are done.

Check an item only once it's merged to `master` and passing CI, not when
it's "basically working locally." Update the status table in
`docs/roadmap.md` when an entire phase's boxes are checked.

---

## Definition of Done — per Django app

Apply this to every app below before checking it off:

- [ ] Models defined (`TenantScopedModel`/`TimeStampedModel`/`SoftDeleteModel` from `core` where applicable)
- [ ] Migrations generated and applied cleanly on a fresh DB
- [ ] `services.py` (writes) and `selectors.py` (reads) implemented — no other app reaches into this app's ORM directly
- [ ] DRF serializers + viewsets + router registered under `/api/v1/`
- [ ] Admin registration where useful for support/ops
- [ ] Permission classes applied (`IsAuthenticated` + tenant scoping + role checks)
- [ ] Unit tests for `services`/`selectors`; integration tests for API endpoints
- [ ] `import-linter` contract passes — no illegal cross-layer imports
- [ ] Added to `LOCAL_APPS` in `backend/config/settings/base.py`
- [ ] OpenAPI schema renders cleanly via `drf-spectacular`

---

## Phase 0 — Scaffolding ✅ DONE

- [x] Django backend skeleton (config/apps split, DRF, JWT, Celery)
- [x] React/Vite/TS frontend skeleton (app shell, boundary-enforced structure, Tailwind v4)
- [x] Docker Compose stack (postgres/redis/minio/backend/celery/frontend/nginx) + dev/prod overrides
- [x] CI pipeline (ruff, import-linter, eslint, tsc, image builds)
- [x] Design docs: architecture, modules, database, api-design, authentication, permissions, multitenancy, deployment, project-structure, frontend-architecture
- [x] vision.md, roadmap.md, coding-standards.md, ui-guidelines.md

---

## Phase 1 — Platform Foundation (current phase)

### Layer 0 apps — build in this exact order

- [x] `core` — `TimeStampedModel`, `SoftDeleteModel`, `TenantScopedModel` (+ `TenantScopedSoftDeleteModel` composing both), UUIDv7 PK, `current_institution`/`correlation_id_ctx` context vars, `StandardPageNumberPagination`, `ConflictError`, `CorrelationIdMiddleware` + JSON logging filter. No API surface or migrations (abstract models only) — verified via ruff, `manage.py check`, `makemigrations --check`, `pytest` (12/12), `lint-imports`, and a live `/healthz/` request.
- [x] `institutions` — `Institution`, `InstitutionCurriculum`, `Domain`, `AcademicCalendarSettings`; `selectors.get_institution_by_domain`; `services.provision_institution`/`set_isolation_tier`/`add_custom_domain`/`verify_domain`; `TenantMiddleware`; `TenantDBRouter` (added to `core`, since it only duck-types `institution.isolation_tier`/`db_alias` and needs no import of `institutions`). `PLATFORM_HOSTS` setting added. Seeding the admin User/InstitutionMembership + welcome notification in `provision_institution`, and the live `upgrade_isolation_tier` runbook, are explicitly deferred until `accounts`/`permissions`/`notifications_core` exist. Verified via ruff, `manage.py check`, `makemigrations`/`migrate`, `pytest` (40/40 across `core`+`institutions`), `lint-imports` (new core↔institutions layer contract kept), and live requests confirming `/healthz/` still works and an unresolved tenant host 404s.
- [ ] `accounts` — custom `User` (email/phone login, no username), registration, password reset
- [ ] `permissions` — `Role`, `Permission`, `InstitutionMembership`; `IsInstitutionMember`/`HasRole` permission classes
- [ ] `audit` — append-only `AuditLog`; signal wiring on sensitive models (finance, grading, role assignment — none exist yet, but the hook point should)
- [ ] `notifications_core` — `NotificationTemplate`, `NotificationLog`, pluggable channel backends; `services.send(...)` always via Celery

### Cross-cutting wiring that rides along with the apps above

- [ ] `AUTH_USER_MODEL = "accounts.User"` set **before the first migration runs** — cannot be changed after
- [ ] `TenantMiddleware` (request-local, not thread-local) added to `MIDDLEWARE`
- [ ] `CorrelationIdMiddleware` added to `MIDDLEWARE`
- [ ] `TenantDBRouter` wired for the dedicated-DB isolation tier
- [ ] `TenantQuerySet`/manager mixin auto-filters by bound tenant on every Layer 1+ model going forward
- [ ] JWT flow verified end-to-end: login, refresh, rotation, blacklist-after-rotation
- [ ] Health-check endpoint for Nginx/uptime monitoring
- [ ] Dashboard shell — empty per-role portal pages wired into `router.tsx`, no data yet
- [ ] Frontend: login screen, password reset screen, route guards per role

### Milestone

- [ ] A fully operational SaaS platform capable of hosting multiple schools securely

---

## Phase 2 — Core Academic Engine

- [ ] `classes_streams` — `AcademicYear`, `Term`, `ClassGrade`, `Stream`, `ClassTeacherAssignment` (build first — almost everything else depends on `get_current_term`)
- [ ] `students` — `Student`, `Enrollment`, `GuardianRelationship`
- [ ] `staff` — `StaffProfile`, department assignment
- [ ] `parents` — `ParentProfile`, portal preferences (reads guardian links from `students`, no duplication)
- [ ] `academics` — abstract `AssessmentEngine`/`ReportEngine` contracts, `GradingScale`, `get_curriculum_engine` resolver stub
- [ ] `timetable` — `Timetable`, `Period`, `SubjectSlotAssignment`, clash detection in `services.assign_slot`
- [ ] `attendance` — `AttendanceRecord` (student/staff), policy config
- [ ] `admissions` — `Application`, `ApplicationStage`, `Offer`; `services.convert_to_enrollment` calling into `students`

### Milestone

- [ ] Schools can fully manage their academic structure before curriculum-specific features are introduced

---

## Phase 3 — Curriculum Plugin Framework

- [ ] Curriculum registry + plugin loader
- [ ] `academics.selectors.get_curriculum_engine(institution)` fully resolves based on `institution.curriculum_type`
- [ ] Plugin SDK: interface, validation, testing framework, version compatibility
- [ ] `curriculum_cbc` — Learning Areas, Competencies, Core Values, PCIs, Projects, Continuous Assessment, Performance Levels, report cards
- [ ] `curriculum_844` — Subjects, CATs, Midterms, End Terms, ranking, mean grades, KCPE/KCSE import
- [ ] `curriculum_british` — EYFS, Key Stages, Year Groups, IGCSE, A-Level, Coursework, Predicted Grades
- [ ] `curriculum_tvet` — Courses, Competency Units, Workshops, Practical Exams, Industrial Attachment, Certification
- [ ] `curriculum_university` — Faculties, Schools, Departments, Programmes, Units, Course Registration, GPA/CGPA, Dissertation, Graduation
- [ ] Verify: none of Layer 1/3 code imports a `curriculum_*` app directly (only through the resolver)

### Milestone

- [ ] EduCore supports multiple education systems through interchangeable curriculum plugins without modifying the core platform

---

## Phase 4 — Finance

- [ ] `finance` — `FeeStructure`, `Invoice`, `Payment`, `Receipt`, `InstallmentPlan`, `Scholarship`, `Payroll`, `ExpenseRecord`
- [ ] M-Pesa payment integration
- [ ] Bank payment recording
- [ ] Cash payment recording
- [ ] Financial reports
- [ ] Audit-log signals confirmed firing on every finance write (compliance-sensitive per `docs/architecture.md` §6)

### Milestone

- [ ] Schools can fully manage their financial operations

---

## Phase 5 — Communication

- [ ] `communication` — `Announcement`, `Circular`, `MessageThread`; `services.publish_announcement` fans out via `notifications_core`
- [ ] SMS backend (e.g. Africa's Talking) live in `notifications_core`
- [ ] Email backend live
- [ ] Push notification framework
- [ ] Notification scheduling
- [ ] Message templates

### Milestone

- [ ] Real-time communication across the institution

---

## Phase 6 — Operations

- [ ] `library` — Book, Copy, Loan, Reservation, Fine
- [ ] `inventory` — Asset, StockItem, StockMovement, Supplier
- [ ] `clinic` — HealthRecord, ClinicVisit, Medication (nurse-role-restricted selectors)
- [ ] `documents` — Document, DocumentCategory, generic-FK attach point

### Milestone

- [ ] Administrative departments become fully digitized

---

## Phase 7 — Campus Services

- [ ] `transport` — Vehicle, Route, Stop, TransportAssignment
- [ ] `hostel` — Hostel, Room, BedAllocation

### Milestone

- [ ] Complete campus management capabilities

---

## Phase 8 — Analytics & Reporting

- [ ] `analytics` — Celery-driven rollups (attendance rate, fee collection %, mean grade trends), read-only against Layer 1/2
- [ ] `reports` — PDF generation (WeasyPrint or similar), stores via `documents.services.attach`
- [ ] `dashboard` — per-portal aggregate facades (Principal, Teacher, Parent, Student dashboards)
- [ ] Exports: PDF, Excel, CSV

### Milestone

- [ ] Institution leadership gains actionable insights through analytics and reporting

---

## Phase 9 — AI Platform

- [ ] `ai_gateway` — `AIProvider` ABC, settings-driven provider toggle
- [ ] Lesson plan generation
- [ ] Exam generation
- [ ] Automatic report comments
- [ ] Student performance prediction
- [ ] Attendance risk detection
- [ ] Verify: no `curriculum_*` or `reports` code talks to an AI provider directly — only through `ai_gateway`

### Milestone

- [ ] AI becomes a native capability across EduCore

---

## Phase 10 — Enterprise Platform

- [ ] White-labeling (custom branding, themes, logos)
- [ ] Billing — subscription management, plan management, invoicing, payment gateway integration
- [ ] Dedicated-infra tenant provisioning as a scriptable, repeatable operation (per `docs/architecture.md` decision log — not a one-off manual process)
- [ ] Dedicated-database deployments
- [ ] Regional hosting
- [ ] Marketplace — curriculum plugins, third-party integrations, extensions
- [ ] Custom domains
- [ ] SSO
- [ ] Backup & disaster recovery automation
- [ ] Monitoring
- [ ] Audit compliance tooling

### Milestone

- [ ] EduCore becomes a production-ready enterprise SaaS platform capable of serving thousands of institutions across multiple regions

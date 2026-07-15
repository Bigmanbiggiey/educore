# EduCore — Project & Folder Structure

Status: DRAFT — pending approval
Step: 2 of 10

---

## 1. Monorepo

**Decision:** Single repository containing `backend/`, `frontend/`, `docker/`, `docs/`.

**Why:** The API contract and its consumer evolve together constantly in an ERP
(new field on Student → new form field, same sprint). A monorepo means one PR
can change both sides atomically, one CI pipeline validates the whole system, and
`docs/api-design.md` stays a single source of truth both teams read. Given this is
presently a single engineering effort (not multiple independent teams shipping on
different cadences), the coordination cost of split repos buys nothing yet. This
can be revisited if the frontend/backend are ever staffed and released independently.

---

## 2. Top-Level Layout

```
educore/
├── backend/                  # Django project — see §3
├── frontend/                 # React SPA — see §4
├── docker/                   # Compose files, Dockerfiles, Nginx config — Step 10
├── docs/                     # This design series + living documentation
├── .github/
│   └── workflows/            # CI: lint, import-linter (boundary check), tests, build
└── README.md
```

---

## 3. Backend Layout (`backend/`)

```
backend/
├── config/                       # Django project package (NOT an app)
│   ├── settings/
│   │   ├── base.py               # shared settings
│   │   ├── dev.py
│   │   ├── staging.py
│   │   └── production.py
│   ├── urls.py                   # mounts /api/v1/ and /admin/
│   ├── asgi.py
│   ├── wsgi.py
│   └── celery.py                 # Celery app instance + autodiscovery
│
├── apps/
│   ├── core/                     # Layer 0 — shared kernel, see docs/modules.md
│   ├── institutions/             # Layer 0
│   ├── accounts/                 # Layer 0
│   ├── permissions/              # Layer 0
│   ├── audit/                    # Layer 0
│   ├── notifications_core/       # Layer 0
│   │
│   ├── students/                 # Layer 1
│   ├── staff/
│   ├── parents/
│   ├── classes_streams/
│   ├── attendance/
│   ├── timetable/
│   ├── finance/
│   ├── library/
│   ├── inventory/
│   ├── transport/
│   ├── hostel/
│   ├── clinic/
│   ├── documents/
│   ├── communication/
│   ├── admissions/
│   ├── academics/                # Layer 1 — curriculum-agnostic contracts (see modules.md)
│   │
│   ├── curriculum_cbc/           # Layer 2
│   ├── curriculum_844/
│   ├── curriculum_british/
│   ├── curriculum_tvet/
│   ├── curriculum_university/
│   │
│   ├── analytics/                # Layer 3
│   ├── reports/
│   ├── dashboard/
│   └── ai_gateway/
│
├── api/
│   └── v1/
│       └── urls.py               # aggregates every app's router under /api/v1/
│
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── production.txt
│
├── manage.py
├── entrypoint.sh                 # migrate --check, collectstatic, gunicorn
├── Dockerfile
└── .importlinter                 # CI-enforced layer boundary contracts, see §5
```

### Standard internal structure of every app

```
students/
├── __init__.py
├── apps.py
├── models.py            # or models/ package if the app outgrows one file
├── services.py          # PUBLIC write interface — the only way other apps mutate this app's state
├── selectors.py          # PUBLIC read interface — the only way other apps query this app's state
├── serializers.py
├── views.py
├── urls.py
├── permissions.py        # app-specific DRF permission classes
├── admin.py
├── tasks.py              # Celery tasks owned by this app
├── signals.py
├── migrations/
└── tests/
    ├── test_models.py
    ├── test_services.py
    └── test_api.py
```

**Rule:** other apps may only import `X.services` and `X.selectors` from app `X`
(plus `X.models` where a genuine FK target is needed — Django requires this). Direct
imports of `X.views`, reaching into `X.models` to build ad-hoc querysets, or copying
business logic instead of calling `X.services.do_thing()` are boundary violations.

---

## 4. Frontend Layout (`frontend/`)

```
frontend/
├── src/
│   ├── app/
│   │   ├── providers/          # QueryClientProvider, AuthProvider, ThemeProvider
│   │   ├── router.tsx          # root route tree, lazy-loaded per portal
│   │   └── ErrorBoundary.tsx
│   │
│   ├── portals/                # one folder per role — composition only, no business logic
│   │   ├── system-admin/
│   │   ├── institution-admin/
│   │   ├── principal/
│   │   ├── finance-officer/
│   │   ├── teacher/
│   │   ├── parent/
│   │   ├── student/
│   │   ├── librarian/
│   │   ├── nurse/
│   │   ├── receptionist/
│   │   ├── transport-manager/
│   │   └── hostel-warden/
│   │       ├── routes.tsx      # this portal's route subtree
│   │       ├── nav.ts          # nav items this role sees
│   │       └── DashboardPage.tsx
│   │
│   ├── features/               # mirrors backend Layer 1/2 apps — actual UI + logic lives here
│   │   ├── students/
│   │   │   ├── api/            # TanStack Query hooks (useStudent, useCreateStudent…)
│   │   │   ├── components/
│   │   │   ├── forms/          # React Hook Form + Zod schema per form
│   │   │   ├── types.ts
│   │   │   └── index.ts        # public exports — same boundary discipline as backend
│   │   ├── finance/
│   │   ├── attendance/
│   │   ├── curriculum-cbc/
│   │   ├── curriculum-844/
│   │   ├── curriculum-british/
│   │   ├── curriculum-tvet/
│   │   ├── curriculum-university/
│   │   └── ... (one per backend app that has UI surface)
│   │
│   ├── shared/
│   │   ├── components/         # design system: Button, Table, Modal, DataGrid…
│   │   ├── hooks/
│   │   ├── lib/                 # api client (fetch wrapper + interceptors), query client config
│   │   └── utils/
│   │
│   ├── styles/
│   └── main.tsx
│
├── public/
├── index.html
├── vite.config.ts
├── tailwind.config.ts
└── tsconfig.json
```

**Portals compose, features implement.** A portal folder should contain almost no
logic — it picks which `features/*` components appear in nav and on the dashboard
for that role. This prevents the classic "FinanceOfficerInvoiceTable" /
"AdminInvoiceTable" duplication problem: there is one `features/finance` invoice
table, and portals decide whether to show it and with which permissions-gated actions.

---

## 5. Boundary Enforcement (CI-checked, not just reviewed)

`backend/.importlinter` will define contracts once code exists, roughly:

```ini
[importlinter]
root_package = apps

[importlinter:contract:layers]
name = Layered architecture
type = layers
layers =
    apps.analytics | apps.reports | apps.dashboard | apps.ai_gateway
    apps.curriculum_cbc | apps.curriculum_844 | apps.curriculum_british | apps.curriculum_tvet | apps.curriculum_university
    apps.students | apps.staff | apps.parents | apps.classes_streams | apps.attendance | apps.timetable | apps.finance | apps.library | apps.inventory | apps.transport | apps.hostel | apps.clinic | apps.documents | apps.communication | apps.admissions | apps.academics
    apps.core | apps.institutions | apps.accounts | apps.permissions | apps.audit | apps.notifications_core
```

`import-linter` fails CI if a lower layer imports from a higher one, or if a
sibling app imports another sibling's `models`/`views` directly instead of going
through `services`/`selectors`. This turns the architecture doc from "guidance
engineers are supposed to remember" into something the build enforces — the same
principle as tenant-filtering being structural rather than conventional in
`docs/architecture.md` §5.

---

## 6. Testing Convention

Tests live inside each app (`tests/` package), not a parallel top-level tree —
keeps a test next to the code it exercises and gets deleted automatically if the
app is ever removed. Frontend tests colocate with the feature (`features/x/*.test.tsx`).

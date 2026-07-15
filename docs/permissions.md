# EduCore — Permissions Design

Status: DRAFT — pending approval
Step: 8 of 10

Data model (`Role`, `Permission`, `InstitutionMembership`, `MembershipRole`)
was fixed in `docs/database.md` §2. This document covers how permissions are
assigned by default, how they're checked per request, and the one deliberate
exception to tenant isolation the system contains.

---

## 1. Permission Code Convention

`{app}.{resource}.{action}`, e.g. `finance.invoice.create`,
`academics.assessment.record`, `admissions.application.convert`. Action verbs
are `view`, `create`, `update`, `delete` for standard CRUD, plus named verbs
for RPC-style actions that mirror the endpoint (`docs/api-design.md` §1) —
the permission code and the `services.py` function it gates should be
readable as the same operation.

**Addition to `Permission` (extends `docs/database.md` §2):**
| Field | Type | Notes |
|---|---|---|
| scope | enum(`platform`, `institution`) | `platform`-scoped permissions (e.g. `institutions.institution.provision`) are never assignable to an institution-defined custom role — enforced at the `Role`/`RolePermission` write path, not just a UI hint |

---

## 2. Seeded System Roles

The 12 portal roles from the project brief are seeded as `Role(is_system=True,
institution=None)` — global templates every institution gets by default —
via a data migration at platform install, not manually created per tenant:

System Administrator, Institution Administrator, Principal, Deputy Principal,
Finance Officer, Teacher, Parent, Student, Librarian, Nurse, Receptionist,
Transport Manager, Hostel Warden.

Institution Administrators may additionally define **custom roles**
(`Role(institution=<their institution>)`) composed from the `institution`-scoped
permission catalog — covers real cases like an "Exams Coordinator" role that
doesn't map to any seeded template, without needing a platform release to add it.

---

## 3. Two Layers of Access Control: RBAC + Object Scope

Role-based permission checks answer "can this role do this *kind* of thing,"
but several roles need narrower scoping than "every record in the
institution" — role alone is not enough:

| Role | Role permission grants | Additional object-scope restriction |
|---|---|---|
| Teacher | `attendance.record.create`, `academics.assessment.record`, etc. | only for classes/subjects they're assigned to teach (`staff.selectors.get_assigned_classes`) — **not** the whole school |
| Parent | `students.student.view`, `finance.invoice.view`, etc. | only their own children (`students.selectors.get_guardian_children`) |
| Student | `students.student.view` (self), `academics.report.view` (self) | only their own record |

This is enforced as a **second filter layered on top of RBAC**, not folded
into the permission check itself — a `TeacherScopedToOwnClasses`,
`ParentScopedToOwnChildren`, or `StudentScopedToSelf` filter applied at the
selector/queryset level, in addition to the `HasPermission(code)` check at
the view level. Two independent layers rather than one combined check is
deliberate defense in depth: a bug in the permission class doesn't
automatically mean a bug in the queryset scope, and vice versa — both would
have to fail simultaneously for a Teacher to see another class's students.

---

## 4. Representative Default Grants

Not the full ~200+ permission-code matrix (finalized per module at
implementation time), but the pattern each role follows:

| Role | Broad grant pattern |
|---|---|
| Institution Administrator | `*.*` within their institution — the highest non-platform role |
| Principal / Deputy Principal | read-broad across all modules; write on academics approval, staff, admissions; finance is **view-only** (approval workflows, not direct payment recording) |
| Finance Officer | full `finance.*`; `students.student.view` / `staff.staff.view` for lookup only |
| Teacher | scoped `attendance.*`, `academics.assessment.*`, `timetable.*.view` — see §3 for the object-scope restriction |
| Parent | `*.view` scoped to own children only, plus `communication.message.create` |
| Student | `*.view` scoped to self only, plus own-profile updates |
| Librarian | full `library.*`; `students.student.view` for lookup |
| Nurse | full `clinic.*`; `students.student.view` for lookup — see §5 for extra handling |
| Receptionist | `admissions.inquiry.*`, `communication.announcement.view`, light `students.student.view` |
| Transport Manager | full `transport.*` |
| Hostel Warden | full `hostel.*` |

---

## 5. Sensitive Data: Health Records (Kenya Data Protection Act, 2019)

`clinic` data is a special category under Kenya's Data Protection Act — it
gets stricter defaults than the general RBAC model:
- Visibility is **opt-in even within otherwise-permitted roles**: a Class
  Teacher does not automatically see a student's `HealthRecord` just because
  they can see the student's academic record — clinic data requires the
  explicit `clinic.record.view` grant, which is not part of the default
  Teacher template.
- **Reads are audited, not just writes** — a deliberate exception to the
  general rule in `docs/modules.md`'s `audit` app (which fires on mutations).
  Who *viewed* a health record is itself compliance-relevant here, so
  `clinic` views also call `audit.services.log_action(...)`.
- This pattern (opt-in visibility + read-auditing) is the template to apply
  to any future module handling another sensitive category (e.g. disciplinary
  records), not a one-off special case specific to `clinic`.

---

## 6. Enforcement & Caching

DRF permission classes compose per view:
`IsAuthenticated, IsInstitutionMember, HasPermission('finance.invoice.view')`
(+ an object-scope filter class where §3 applies). All must pass.

Membership + role + permission lookups are cached in Redis, keyed
`perm:{user_id}:{institution_id}`, 5-minute TTL, **explicitly invalidated**
by `permissions.services.assign_role(...)` and `services.revoke_role(...)`
on write — not left to expire naturally when access is being actively
revoked (e.g. during a security incident, revocation must be immediate, not
"within 5 minutes"). This is the caching layer referenced as the mitigation
in `docs/authentication.md` §2 for why the JWT itself can stay thin without
a DB round trip on every single request in the common case.

---

## 7. The One Deliberate Exception: System Administrator

Every other role operates inside `TenantScopedModel`'s auto-filtering
(`docs/architecture.md` §5) — there is structurally no way to see another
institution's data. **System Administrator is the one role that must, by
job function, act across tenants** (provisioning institutions, managing
isolation tiers, platform-level support). This is treated as a hole that
must be deliberately narrow and fully accountable, not an ambient superuser
capability:

- `is_platform_staff=True` grants access to platform-level endpoints
  (`institutions.institution.provision`, etc. — all `scope=platform`
  permissions, §1) on the dedicated `admin.educore.africa` host only. It
  does **not** grant blanket read access to every institution's tenant data.
- To view or act within a specific institution's data, a System Admin must
  explicitly start a scoped, time-boxed session:
  ```
  POST /api/v1/platform/admin/act-as/{institution_id}/
    → short-lived (30 min) elevated context, NOT a new login,
      audit-logged as platform.admin.impersonate_start
  ```
  Every action taken during that window is audited with an explicit
  `acting_as_admin=true` flag distinguishing it from a normal institution
  user's action. The frontend renders a persistent, impossible-to-miss
  banner ("Viewing as System Admin inside St. Mary's") for the entire
  duration — this must never be ambiguous to whoever's watching the screen.
  The session ends automatically at the 30-minute mark or on explicit exit
  (`platform.admin.impersonate_end`, also audited).
- **Why "break glass" instead of just giving System Admin a bypass flag on
  `TenantScopedModel`'s manager:** a silent bypass is invisible in the audit
  log and invisible in the UI — exactly the two places a compliance review
  or incident investigation would look first. Making elevated access an
  explicit, time-limited, loudly-visible action turns "who accessed this
  school's data and why" from a forensic question into a queryable fact.

---

## 8. What This Document Deliberately Defers

- The full permission-code catalog per app → generated alongside each
  module's `services.py`/`selectors.py` at implementation time (permission
  codes should be named to match the functions they gate, so this is
  sequenced with implementation, not ahead of it).
- Institution Administrator's custom-role UI/UX → part of the
  `institutions`/`permissions` app frontend build, not an architectural
  decision.

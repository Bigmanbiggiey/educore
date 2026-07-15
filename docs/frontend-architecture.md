# EduCore — React Frontend Architecture

Status: DRAFT — pending approval
Step: 4 of 10

Folder layout was fixed in `docs/project-structure.md` §4. This document covers
the technical architecture that lives inside that layout: routing, state,
auth, forms, theming, and the rules that keep 12 portals from turning into 12
divergent codebases.

---

## 1. Routing & Portal Composition

One root router (`app/router.tsx`) mounts a lazy-loaded subtree per portal:

```
/login
/auth/callback
/:portalSlug/*        → lazy(() => import('portals/<slug>/routes'))
```

- After login, the API returns the user's `InstitutionMembership` role(s). If a
  user has exactly one role at one institution, they land directly in that
  portal. If they have multiple (e.g. a Principal who's also a parent), they
  see a lightweight portal picker — this is a real case given `accounts` is
  identity-only and membership is many-to-many (`docs/modules.md`).
- Each portal's route subtree is **code-split at the portal boundary**, not
  just per-page. A Librarian's session never downloads Payroll or Hostel
  bundles. This matters more here than in a typical SPA because the union of
  all 12 portals' features is genuinely large.
- Route guards check `HasRole`/`IsInstitutionMember` client-side for UX only
  (hiding nav, redirecting) — this is **never** the authorization boundary.
  The API enforces permissions server-side regardless of what the client
  renders (`docs/architecture.md` §6). Client-side checks that aren't
  backed by an equivalent server check are a bug, not a convenience.

---

## 2. Auth on the Frontend

Backend issues JWT access + refresh (Step 7 will detail the backend side).
Frontend contract:
- **Access token:** held in memory (a module-level variable in
  `shared/lib/auth.ts`), never in `localStorage`/`sessionStorage`. Lost on
  hard refresh by design.
- **Refresh token:** httpOnly, `Secure`, `SameSite=Strict` cookie — invisible
  to JS entirely, set by the backend. This is why it survives a hard refresh
  when the access token doesn't: on app boot, `shared/lib/auth.ts` silently
  calls `/api/v1/auth/refresh/` to mint a new access token before rendering
  any protected route.
- **401 handling:** the API client wrapper (`shared/lib/api.ts`) intercepts a
  single 401, attempts one silent refresh, retries the original request once,
  and only then redirects to `/login`. This logic lives in exactly one place
  — no feature-level code ever handles token refresh itself.
- **Why not localStorage for the access token:** an XSS in any one feature
  (and with 12 portals' worth of surface area, that risk compounds) would
  otherwise be a full account takeover with a persistent token. Memory-only
  access tokens cap the blast radius to the current tab session.

---

## 3. Server State — TanStack Query

- Every `features/*/api/` hook wraps one backend endpoint. Query keys follow
  `[featureName, resourceName, params]`, e.g. `['finance', 'invoices', {studentId}]`
  — consistent enough that invalidation can target a feature broadly
  (`queryClient.invalidateQueries(['finance'])` after a payment) or narrowly.
- Tenant scoping is implicit: the API resolves institution from the request's
  `Host` header (`docs/architecture.md` §5), so query keys don't need an
  institution segment. This also means query caches naturally don't need
  manual clearing on institution switch — a full navigation to a different
  portal subdomain is a full page load anyway.
- Mutations use optimistic updates only where a wrong optimistic guess is
  cheap to undo and low-stakes (e.g. marking attendance, toggling a read
  flag). Finance and grading mutations are **not** optimistic — they wait for
  server confirmation, because showing a payment or grade that then reverts
  is worse than a half-second of latency.
- Global `QueryClient` config: `staleTime` defaults conservatively (30s) for
  most resources but is set near-zero for finance balances and near-`Infinity`
  for rarely-changing reference data (e.g. `classes_streams` term list),
  configured per-hook, not globally overridden ad hoc.

---

## 4. Forms — React Hook Form + Zod

- Every form's validation schema lives in `features/<x>/forms/<name>.schema.ts`
  as a Zod schema, and the TypeScript type is inferred from it
  (`type StudentFormValues = z.infer<typeof studentSchema>`) — one definition,
  never a hand-written interface that can drift from validation rules.
- Where a Zod schema's shape mirrors a DRF serializer closely (which it will,
  often), that's expected duplication, not a violation — client validation
  must never be the only validation (`docs/api-design.md`, Step 6, will fix
  the server side as the actual source of truth). Zod here is a UX layer:
  fast feedback, not a security boundary.
- Curriculum-specific forms (e.g. CBC competency entry vs 8-4-4 CAT entry)
  live in their respective `features/curriculum-*` folders and are selected
  at render time based on the institution's curriculum type — the frontend
  mirrors the backend's `academics.selectors.get_curriculum_engine()` pattern
  with a small `getCurriculumFormSet(curriculumType)` resolver in
  `features/academics/`, so gradebook UI doesn't branch on curriculum type
  inline either.

---

## 5. Component Architecture

- `shared/components/` is the **only** place primitive UI is built (Button,
  Table, Modal, DataGrid, FormField). This is the frontend equivalent of the
  backend's layer rule: a feature may compose primitives, but may not build a
  second `Button` because its portal wants slightly different padding —
  that's a variant prop on the shared component, not a fork.
- `features/*` may not import from other `features/*` directly. If
  `curriculum-cbc` needs something from `students`, it goes through
  `features/students/index.ts`'s public exports — same discipline as backend
  `services.py`/`selectors.py`, enforced by an ESLint import-boundary rule
  (`eslint-plugin-boundaries`) rather than convention.
- `portals/*` compose `features/*` and contain no business logic of their
  own — just nav config and page assembly, as fixed in `project-structure.md`.

---

## 6. Theming & Per-Institution Branding

- Tailwind v4 with CSS custom properties for the color palette
  (`--color-primary`, `--color-surface`, etc.), not hard-coded Tailwind
  color classes in components — this is what makes both dark mode *and*
  per-institution branding possible through the same mechanism.
- `institutions.Institution` (backend) carries a branding record (logo,
  primary color, favicon). On login, the frontend applies it by setting CSS
  variables on `:root` — one theming pipeline serves both "dark mode" and
  "St. Mary's brand colors," rather than two separate systems.
- Dark mode: `prefers-color-scheme` by default, with a user-level override
  stored server-side (part of user preferences, not just local storage) so
  it persists across devices.

---

## 7. API Client Layer

Single fetch wrapper (`shared/lib/api.ts`) is the only code in the frontend
that constructs a request to the backend. Responsibilities: attach auth
header, handle the 401→refresh→retry flow (§2), normalize error shape to
match `docs/api-design.md`'s error contract (Step 6), and attach a
correlation ID header echoed by the backend's structured logging
(`docs/architecture.md` §6) so a bug report can be traced from a browser
console error to a specific backend log line.

---

## 8. Error Handling & Loading States

- One `ErrorBoundary` per portal subtree (not per page) — a crash in one
  feature's component doesn't take down the whole portal shell (nav stays
  usable).
- TanStack Query's `isPending`/`isError` drive consistent skeleton/error UI
  via shared `<QueryBoundary>` wrapper in `shared/components`, rather than
  every feature hand-rolling loading spinners.

---

## 9. Accessibility & Responsiveness Baseline

- All `shared/components` primitives are built on accessible foundations
  (proper ARIA roles, keyboard navigation, focus management) once, so every
  feature inherits it rather than re-implementing per form/table.
- Mobile-responsive down to a single-column layout is required for Parent
  and Student portals specifically (highest likelihood of phone-only access
  in the Kenyan market context); Admin-heavy portals (Finance, System Admin)
  can reasonably assume tablet/desktop as primary but must not break on
  mobile.

---

## 10. Testing

Component/unit tests colocate with features (`features/x/*.test.tsx`), using
Vitest + React Testing Library. Critical cross-portal flows (login → role
routing, payment submission, report generation) get a thin layer of E2E
coverage (Playwright) — full E2E coverage of all 12 portals is not a v1 goal;
this is chosen deliberately narrow, not an oversight, and should be revisited
once real usage patterns show which flows actually break in practice.

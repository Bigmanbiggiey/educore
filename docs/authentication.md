# EduCore — Authentication Design

Status: DRAFT — pending approval
Step: 7 of 10

Identity model (`accounts.User`) was fixed in `docs/database.md` §2 — email or
phone login, no username, platform-global (no `institution_id`). This
document covers how a session actually gets established and stays valid.

---

## 1. Token Strategy

- **Access token:** JWT, `HS256`, 15-minute lifetime.
- **Refresh token:** rotating JWT, 7-day lifetime, httpOnly/Secure/SameSite=Strict
  cookie (`docs/frontend-architecture.md` §2), blacklisted on rotation and on logout
  (`rest_framework_simplejwt.token_blacklist`).
- **Why `HS256`, not `RS256`:** `RS256` (asymmetric) only earns its complexity
  when a party *other than the issuer* needs to verify tokens independently —
  e.g. a split-out microservice, or a third party validating tokens without
  trusting a call back to EduCore. Neither is true today: this is a monolith
  verifying its own tokens. `HS256` with a per-deployment secret (rotatable,
  stored outside the repo) is simpler and equally secure for this shape. If a
  service is ever extracted from the monolith, migrating to `RS256` at that
  point is a contained change — this isn't a decision that paints us into a
  corner, just the right complexity for the system as it exists now (YAGNI).
- **Rotation as a compromise signal:** each refresh issues a new refresh
  token and blacklists the old one. If a blacklisted refresh token is ever
  presented again, that's a strong signal of token theft (someone replaying
  a stolen token after the legitimate client already rotated past it) — this
  event triggers revocation of the entire token family (all tokens issued
  from that login), not just the one request.

---

## 2. What's In the Token — Deliberately Thin

The JWT carries only `sub` (user id), `jti`, `exp`, `token_type`. **It does
not carry institution membership, roles, or permissions.**

This is a specific trade-off, not an oversight: embedding roles would save a
DB lookup per request, but roles/membership are re-verified against the
database (via a short-TTL Redis cache, see `docs/permissions.md` §6) on
every request instead. Reasoning:
- A 15-minute access token embedding a role would mean a role change (e.g.
  an admin suspends a compromised account, or revokes a Finance Officer's
  access mid-incident) doesn't take effect for up to 15 minutes. For a
  finance/grading system, "revoke access, but maybe not for 15 minutes" is
  not an acceptable security property.
- It also keeps `docs/api-design.md` §7's rule intact — no institution
  context travels in client-controlled material (token claims are technically
  server-issued, but the principle holds: institution binding happens fresh,
  server-side, every request, via `Host` header + DB check, never trusted
  from something issued minutes ago).

---

## 3. Login Flow

```
POST /api/v1/auth/login/   { email_or_phone, password }
```
1. `TenantMiddleware` resolves the institution from `Host` (as with every
   request — login is not exempt).
2. Credentials validated against `accounts.User`.
3. `InstitutionMembership` for (user, resolved institution) must exist and
   be `status=active` — a valid password with no active membership at *this*
   hostname fails login here, not later at the first protected endpoint.
4. Access token issued in the response body; refresh token set as a cookie.

```
POST /api/v1/auth/refresh/     (reads refresh cookie)   → new access token + rotated refresh cookie
POST /api/v1/auth/logout/      blacklists current refresh token, clears cookie
GET  /api/v1/auth/me/          current user + this-institution's membership + roles
```

---

## 4. Sessions Are Bound to One Hostname

Because tenant resolution is host-based (`docs/architecture.md` §5) and the
refresh cookie is scoped to the specific hostname that issued it (never a
wildcard `*.educore.africa` cookie), **a session belongs to one institution's
hostname at a time.**

Consequence for multi-membership users (a parent with children at two
schools, or a consultant teacher at two institutions): they authenticate
separately per institution hostname — the same underlying `accounts.User`,
but a distinct session per host, exactly as one would expect logging into
two separate Slack workspaces. This isn't a limitation to work around; it
falls directly out of subdomain-based tenancy and is the safer default —
a cookie compromised on `stmary.educore.africa` is inert on
`kiambuhigh.educore.africa` even for the same platform, same user.

Custom domains (`portal.stmary.sc.ke`) are a different origin entirely, so no
cross-domain cookie sharing is attempted there either — same model, no
special-casing required.

**System Administrator** access lives on its own dedicated host (e.g.
`admin.educore.africa`), authenticated by `is_platform_staff=True` rather
than any `InstitutionMembership` — see §7 for why this is treated as a
deliberately narrow, heavily-audited exception rather than an ambient
capability.

---

## 5. Password & Account Policy

- Django's built-in validators: minimum length 10, common-password check,
  not-too-similar-to-user-attributes, not entirely numeric.
- Password reset: single-use, time-limited (1 hour) token, delivered via
  `notifications_core.services.send(...)` (email or SMS per user preference),
  never via a link that logs the user in directly — reset always requires
  setting a new password. The same `request_password_reset`/
  `confirm_password_reset` pair also serves as the Institution
  Administrator's "set your first password" mechanism when an institution
  is provisioned (`docs/multitenancy.md` §7) — the token neither knows nor
  cares whether it was issued for a forgotten password or a first one.
  **Known gap, not fixed by that work:** the *general* forgot-password
  flow (`PasswordResetRequestView`) still never actually delivers its
  token — `accounts` has no wiring to `notifications_core.services.send(...)`
  for that path (only the new institution-admin-welcome path is wired, via
  `core.signals.notification_requested`, since `accounts` itself can't
  import `notifications_core` directly — independent Layer 0 siblings).
  Existing users requesting a password reset get a token that's created
  but never emailed/texted to them. Follow-up, not in scope here.
- **MFA fields reserved now, enforcement built later:** `accounts.User` gets
  a nullable `totp_secret` and `mfa_enabled` field in the initial migration,
  even though the enrollment/verification flow isn't built for v1. Adding
  these columns later means a migration touching the most sensitive table in
  the system while it holds live user data — cheap to reserve now, riskier
  to retrofit.

---

## 6. Public / Unauthenticated Endpoints

Not everything requires a token. The clearest case: **admissions
applications** — a prospective parent filling out an application typically
has no account yet. `POST /api/v1/admissions/applications/` is public, but
still tenant-resolved via `Host` (a public form on `stmary.educore.africa`
creates an `Application` scoped to that institution, same as any other
write). Protections given it accepts anonymous input:
- Aggressive rate limiting (`docs/api-design.md` §13) tightened further for
  this specific endpoint given its public+anonymous nature.
- Server-side validation only (client Zod validation is UX, never trusted
  — consistent with `docs/frontend-architecture.md` §4).
- CAPTCHA/bot-mitigation is flagged as an open item, deferred until this
  endpoint is actually built and abuse patterns (if any) are observed —
  not designed speculatively now.

---

## 7. Background Jobs Have No Session

Celery tasks are not tied to an HTTP request and therefore never carry a
JWT or any request-scoped tenant context (`docs/architecture.md` §5
explicitly rejects thread-local tenant binding for this reason). A task that
needs institution context receives `institution_id` as an explicit argument
when enqueued, and re-derives everything it needs from the database — the
same discipline as the API never trusting ambient context, applied to
background work too.

---

## 8. Cross-Reference

Full role/permission enforcement, the System Administrator "break glass"
access pattern, and Redis-cached membership lookups are specified in
`docs/permissions.md` (Step 8) — authentication answers "who is this,"
permissions answers "what can they do, and where."

/**
 * Access token lives in memory only, never localStorage — capping XSS
 * blast radius across a 12-portal surface area. Refresh token is an
 * httpOnly cookie the browser handles automatically.
 * See docs/frontend-architecture.md §2.
 *
 * login/logout/silentRefresh call `fetch` directly rather than going
 * through `api.ts`'s wrapper — `api.ts` imports from this module (for the
 * access token + the 401 retry flow), so the reverse would be circular,
 * and semantically these three aren't "call an API resource", they're the
 * primitives that wrapper depends on.
 */

import { ApiError, type ApiErrorBody } from "./api-error";

export interface MeResponse {
  id: string;
  email: string | null;
  phone: string | null;
  is_platform_staff: boolean;
  institution_membership: { roles: string[] } | null;
}

export interface HostContext {
  host_type: "platform" | "institution";
}

let accessToken: string | null = null;

export function getAccessToken(): string | null {
  return accessToken;
}

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export async function fetchHostContext(): Promise<HostContext> {
  const res = await fetch("/api/v1/auth/host-context/");
  if (!res.ok) {
    const body = (await res.json().catch(() => ({}))) as ApiErrorBody;
    throw new ApiError(res.status, body);
  }
  return (await res.json()) as HostContext;
}

export async function login(emailOrPhone: string, password: string): Promise<void> {
  const res = await fetch("/api/v1/auth/login/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ email_or_phone: emailOrPhone, password }),
  });
  if (!res.ok) {
    const body = (await res.json().catch(() => ({}))) as ApiErrorBody;
    throw new ApiError(res.status, body);
  }
  const data = (await res.json()) as { access_token: string };
  setAccessToken(data.access_token);
}

/** Parallel to `login`, not a branch inside it — docs/permissions.md §7's
 * platform-staff login has nothing to do with institution membership. */
export async function platformLogin(emailOrPhone: string, password: string): Promise<void> {
  const res = await fetch("/api/v1/platform/auth/login/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ email_or_phone: emailOrPhone, password }),
  });
  if (!res.ok) {
    const body = (await res.json().catch(() => ({}))) as ApiErrorBody;
    throw new ApiError(res.status, body);
  }
  const data = (await res.json()) as { access_token: string };
  setAccessToken(data.access_token);
}

/** Starts a break-glass session (docs/permissions.md §7) — returns the
 * elevated access token rather than setting it directly, so the caller
 * (`AuthProvider.actAs`) can stash the current platform token first. */
export async function actAs(institutionId: string): Promise<string> {
  const res = await fetch(`/api/v1/platform/admin/act-as/${institutionId}/`, {
    method: "POST",
    headers: { Authorization: `Bearer ${getAccessToken() ?? ""}` },
    credentials: "include",
  });
  if (!res.ok) {
    const body = (await res.json().catch(() => ({}))) as ApiErrorBody;
    throw new ApiError(res.status, body);
  }
  const data = (await res.json()) as { access_token: string };
  return data.access_token;
}

/** Ends a break-glass session — the caller still needs to restore the
 * stashed platform token afterward (`AuthProvider.endActAs`). */
export async function endActAs(): Promise<void> {
  await fetch("/api/v1/platform/admin/act-as/end/", {
    method: "POST",
    headers: { Authorization: `Bearer ${getAccessToken() ?? ""}` },
    credentials: "include",
  });
}

export async function logout(): Promise<void> {
  await fetch("/api/v1/auth/logout/", { method: "POST", credentials: "include" });
  setAccessToken(null);
}

export async function fetchMe(): Promise<MeResponse> {
  const res = await fetch("/api/v1/auth/me/", {
    headers: { Authorization: `Bearer ${getAccessToken() ?? ""}` },
    credentials: "include",
  });
  if (!res.ok) {
    const body = (await res.json().catch(() => ({}))) as ApiErrorBody;
    throw new ApiError(res.status, body);
  }
  return (await res.json()) as MeResponse;
}

export async function silentRefresh(): Promise<boolean> {
  const res = await fetch("/api/v1/auth/refresh/", {
    method: "POST",
    credentials: "include",
  });
  if (!res.ok) {
    setAccessToken(null);
    return false;
  }
  const data = (await res.json()) as { access_token: string };
  setAccessToken(data.access_token);
  return true;
}

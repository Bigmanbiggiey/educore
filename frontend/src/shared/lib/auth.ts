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
  institution_membership: { roles: string[] } | null;
}

let accessToken: string | null = null;

export function getAccessToken(): string | null {
  return accessToken;
}

export function setAccessToken(token: string | null): void {
  accessToken = token;
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

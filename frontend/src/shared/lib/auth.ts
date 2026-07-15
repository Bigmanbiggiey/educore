/**
 * Access token lives in memory only, never localStorage — capping XSS
 * blast radius across a 12-portal surface area. Refresh token is an
 * httpOnly cookie the browser handles automatically.
 * See docs/frontend-architecture.md §2.
 */

let accessToken: string | null = null;

export function getAccessToken(): string | null {
  return accessToken;
}

export function setAccessToken(token: string | null): void {
  accessToken = token;
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

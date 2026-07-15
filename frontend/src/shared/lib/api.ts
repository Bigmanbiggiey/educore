/**
 * The only place in the frontend that constructs a request to the backend.
 * Attaches auth + a correlation ID, retries once on 401 via silent refresh,
 * and normalizes every error response into the shape from
 * docs/api-design.md §4. See docs/frontend-architecture.md §7.
 */

import { getAccessToken, silentRefresh } from "./auth";

interface ApiErrorBody {
  error?: {
    code: string;
    message: string;
    fields?: Record<string, string[]>;
    correlation_id?: string;
  };
}

export class ApiError extends Error {
  status: number;
  code: string;
  fields?: Record<string, string[]>;
  correlationId?: string;

  constructor(status: number, body: ApiErrorBody) {
    super(body.error?.message ?? "Request failed");
    this.status = status;
    this.code = body.error?.code ?? "unknown_error";
    this.fields = body.error?.fields;
    this.correlationId = body.error?.correlation_id;
  }
}

async function request<T>(path: string, options: RequestInit = {}, isRetry = false): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body) headers.set("Content-Type", "application/json");
  headers.set("X-Correlation-Id", crypto.randomUUID());

  const token = getAccessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`/api/v1${path}`, {
    ...options,
    headers,
    credentials: "include",
  });

  if (res.status === 401 && !isRetry) {
    const refreshed = await silentRefresh();
    if (refreshed) return request<T>(path, options, true);
  }

  if (!res.ok) {
    const body = (await res.json().catch(() => ({}))) as ApiErrorBody;
    throw new ApiError(res.status, body);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path, { method: "GET" }),
  post: <T>(path: string, data?: unknown) =>
    request<T>(path, { method: "POST", body: data ? JSON.stringify(data) : undefined }),
  patch: <T>(path: string, data?: unknown) =>
    request<T>(path, { method: "PATCH", body: data ? JSON.stringify(data) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};

/**
 * Uniform error shape from docs/api-design.md §4, shared by `api.ts` (every
 * authenticated request) and `auth.ts` (login, which runs before there's a
 * token to attach — kept out of `api.ts` itself to avoid a circular import,
 * since `api.ts` already imports from `auth.ts`).
 */

export interface ApiErrorBody {
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

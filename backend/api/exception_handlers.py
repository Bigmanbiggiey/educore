"""
Uniform error contract for every API response, per docs/api-design.md §4.
No view should ever hand-roll its own error shape — this is the one place
DRF exceptions are translated into the {"error": {...}} envelope the
frontend's shared/lib/api.ts error normalizer expects.
"""

from rest_framework.views import exception_handler as drf_exception_handler

STATUS_CODE_TO_ERROR_CODE = {
    400: "validation_error",
    401: "unauthenticated",
    403: "permission_denied",
    404: "not_found",
    409: "conflict",
    429: "rate_limited",
}


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        # Unhandled exception (e.g. a genuine 500) — falls through to
        # Django's own error handling; already captured by Sentry/logging
        # (docs/deployment.md §7).
        return None

    request = context.get("request")
    # apps.core.middleware.CorrelationIdMiddleware (Phase 1) sets this;
    # gracefully absent until then.
    correlation_id = getattr(request, "correlation_id", None) if request else None

    code = STATUS_CODE_TO_ERROR_CODE.get(response.status_code, "error")
    fields = None
    message = "An error occurred."

    if isinstance(response.data, dict):
        if set(response.data.keys()) == {"detail"}:
            message = str(response.data["detail"])
        else:
            fields = {
                field: value if isinstance(value, list) else [value]
                for field, value in response.data.items()
            }
            message = "One or more fields are invalid."
    elif isinstance(response.data, list):
        message = " ".join(str(item) for item in response.data)

    error_body = {"code": code, "message": message}
    if fields:
        error_body["fields"] = fields
    if correlation_id:
        error_body["correlation_id"] = correlation_id

    response.data = {"error": error_body}
    return response

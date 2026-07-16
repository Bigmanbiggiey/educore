"""Correlation-ID middleware — docs/architecture.md §6 and
docs/api-design.md §4. api.exception_handlers.custom_exception_handler
already reads `request.correlation_id`; this is what actually sets it.
"""

import uuid

from apps.core.context import correlation_id_ctx

CORRELATION_ID_HEADER = "X-Correlation-ID"


class CorrelationIdMiddleware:
    """Reads an inbound X-Correlation-ID (set by Nginx or an upstream
    caller) or generates one, binds it to the request and to a contextvar
    so structured logging can attach it to every log line for the request
    (docs/architecture.md §6), and echoes it back on the response — so a
    user's bug report traces to one backend log line without guesswork."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        correlation_id = request.headers.get(CORRELATION_ID_HEADER) or str(uuid.uuid4())
        request.correlation_id = correlation_id
        token = correlation_id_ctx.set(correlation_id)
        try:
            response = self.get_response(request)
        finally:
            correlation_id_ctx.reset(token)
        response[CORRELATION_ID_HEADER] = correlation_id
        return response

"""Logging filter that attaches the current request's correlation ID to
every log record — docs/architecture.md §6.
"""

import logging

from apps.core.context import correlation_id_ctx


class CorrelationIdLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = correlation_id_ctx.get() or "-"
        return True

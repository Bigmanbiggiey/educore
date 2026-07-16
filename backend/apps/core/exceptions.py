"""Base DRF exception classes not already covered by
rest_framework.exceptions — docs/api-design.md §5.
"""

from rest_framework import status
from rest_framework.exceptions import APIException


class ConflictError(APIException):
    """DRF ships 400/401/403/404/405/406/415/429/500 but no 409 — used for
    e.g. a duplicate M-Pesa transaction reference (docs/api-design.md §11)."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "The request conflicts with the current state of the resource."
    default_code = "conflict"

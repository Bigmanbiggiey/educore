"""Base pagination — docs/api-design.md §3. Every list endpoint across all
27 apps uses this via REST_FRAMEWORK["DEFAULT_PAGINATION_CLASS"] rather than
each view opting in individually.
"""

from rest_framework.pagination import PageNumberPagination


class StandardPageNumberPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100

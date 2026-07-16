from apps.core.pagination import StandardPageNumberPagination


def test_defaults_match_api_design_conventions():
    # docs/api-design.md §3: "Default page_size=25, client-overridable via
    # ?page_size=, capped at 100."
    assert StandardPageNumberPagination.page_size == 25
    assert StandardPageNumberPagination.page_size_query_param == "page_size"
    assert StandardPageNumberPagination.max_page_size == 100

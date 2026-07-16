from django.http import HttpResponse
from django.test import RequestFactory

from apps.core.context import correlation_id_ctx
from apps.core.middleware import CORRELATION_ID_HEADER, CorrelationIdMiddleware


def test_generates_a_correlation_id_when_none_is_supplied():
    seen = {}

    def get_response(request):
        seen["correlation_id"] = request.correlation_id
        seen["ctx_during_request"] = correlation_id_ctx.get()
        return HttpResponse()

    middleware = CorrelationIdMiddleware(get_response)
    response = middleware(RequestFactory().get("/"))

    assert seen["correlation_id"]
    assert seen["ctx_during_request"] == seen["correlation_id"]
    assert response[CORRELATION_ID_HEADER] == seen["correlation_id"]
    # Reset after the request — must never leak into the next request
    # handled by the same worker (docs/multitenancy.md §2's same rationale,
    # applied to logging context rather than tenant context).
    assert correlation_id_ctx.get() is None


def test_echoes_an_inbound_correlation_id_instead_of_replacing_it():
    def get_response(request):
        return HttpResponse()

    middleware = CorrelationIdMiddleware(get_response)
    request = RequestFactory().get("/", HTTP_X_CORRELATION_ID="client-supplied-id")
    response = middleware(request)

    assert request.correlation_id == "client-supplied-id"
    assert response[CORRELATION_ID_HEADER] == "client-supplied-id"

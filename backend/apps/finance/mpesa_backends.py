"""Pluggable M-Pesa gateway backend — Phase 4 Stage 2 (docs/roadmap.md),
same settings-driven "swap the implementation without touching call sites"
shape as `apps.notifications_core.backends.NotificationChannelBackend`/
`get_backend()`.

`FakeMpesaGatewayBackend` is the dev/test default (no network, mirrors
`ConsoleChannelBackend`'s role) — a real deployment opts into
`DarajaGatewayBackend` explicitly via `MPESA_GATEWAY_BACKEND` in `.env`.
"""

from __future__ import annotations

import base64
import uuid
from abc import ABC, abstractmethod
from decimal import Decimal

import requests
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.utils.module_loading import import_string

_ACCESS_TOKEN_CACHE_KEY = "mpesa:access_token"
_REQUEST_TIMEOUT_SECONDS = 10


class MpesaGatewayError(Exception):
    """Raised on any failure to initiate an STK Push — a bad phone number,
    an auth failure, an unreachable gateway, or a non-zero Daraja response
    code. The caller (`services.initiate_mpesa_stk_push`) is what turns
    this into a `FAILED` `MpesaSTKPushRequest` row rather than a silently
    retried/crashed request — same "raises on failure, caller logs it"
    contract as `NotificationChannelBackend.send`."""


class MpesaGatewayBackend(ABC):
    @abstractmethod
    def initiate_stk_push(
        self,
        *,
        phone_number: str,
        amount: Decimal,
        account_reference: str,
        transaction_desc: str,
        callback_url: str,
    ) -> dict:
        """Sends the STK Push request and returns
        `{"merchant_request_id": ..., "checkout_request_id": ...}`. Raises
        `MpesaGatewayError` on failure. Does not itself confirm payment —
        that only ever happens via the callback Safaricom sends to
        `callback_url` later (`webhooks.MpesaCallbackView`)."""


class FakeMpesaGatewayBackend(MpesaGatewayBackend):
    def initiate_stk_push(
        self,
        *,
        phone_number: str,
        amount: Decimal,
        account_reference: str,
        transaction_desc: str,
        callback_url: str,
    ) -> dict:
        return {
            "merchant_request_id": f"fake-merchant-{uuid.uuid4().hex[:12]}",
            "checkout_request_id": f"fake-checkout-{uuid.uuid4().hex[:12]}",
        }


class DarajaGatewayBackend(MpesaGatewayBackend):
    def _base_url(self) -> str:
        if settings.MPESA_ENV == "production":
            return "https://api.safaricom.co.ke"
        return "https://sandbox.safaricom.co.ke"

    def _get_access_token(self) -> str:
        cached = cache.get(_ACCESS_TOKEN_CACHE_KEY)
        if cached is not None:
            return cached
        response = requests.get(
            f"{self._base_url()}/oauth/v1/generate?grant_type=client_credentials",
            auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET),
            timeout=_REQUEST_TIMEOUT_SECONDS,
        )
        if response.status_code != 200:
            raise MpesaGatewayError(
                f"OAuth token request failed: {response.status_code} {response.text}"
            )
        data = response.json()
        token = data["access_token"]
        # Safaricom's token is valid ~1h (3600s) — refresh 5 minutes early
        # rather than racing an in-flight STK Push against expiry.
        expires_in = int(data.get("expires_in", 3600))
        cache.set(_ACCESS_TOKEN_CACHE_KEY, token, max(expires_in - 300, 60))
        return token

    def initiate_stk_push(
        self,
        *,
        phone_number: str,
        amount: Decimal,
        account_reference: str,
        transaction_desc: str,
        callback_url: str,
    ) -> dict:
        timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
        password = base64.b64encode(
            f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}".encode()
        ).decode()
        try:
            token = self._get_access_token()
            response = requests.post(
                f"{self._base_url()}/mpesa/stkpush/v1/processrequest",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "BusinessShortCode": settings.MPESA_SHORTCODE,
                    "Password": password,
                    "Timestamp": timestamp,
                    "TransactionType": "CustomerPayBillOnline",
                    # Safaricom expects a whole-shilling integer amount.
                    "Amount": int(amount),
                    "PartyA": phone_number,
                    "PartyB": settings.MPESA_SHORTCODE,
                    "PhoneNumber": phone_number,
                    "CallBackURL": callback_url,
                    # Daraja caps AccountReference at 12 characters.
                    "AccountReference": account_reference[:12],
                    "TransactionDesc": transaction_desc,
                },
                timeout=_REQUEST_TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            raise MpesaGatewayError(f"STK Push request failed: {exc}") from exc

        data = response.json()
        if response.status_code != 200 or data.get("ResponseCode") != "0":
            raise MpesaGatewayError(
                f"STK Push rejected: {data.get('ResponseDescription', response.text)}"
            )
        return {
            "merchant_request_id": data["MerchantRequestID"],
            "checkout_request_id": data["CheckoutRequestID"],
        }


def get_mpesa_backend() -> MpesaGatewayBackend:
    backend_class = import_string(settings.MPESA_GATEWAY_BACKEND)
    return backend_class()

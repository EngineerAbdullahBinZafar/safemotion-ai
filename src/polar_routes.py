"""
SafeMotion AI — Polar Payments & Webhook Integration
Author: Engineer Abdullah Bin Zafar
"""

import logging
import os
import sys
from pathlib import Path
from typing import Literal

from dotenv import find_dotenv, load_dotenv
from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
import polar
import polar.v2026_10.webhooks
from polar.v2026_10 import Polar
from polar.v2026_10.webhooks import (
    PolarWebhookError,
    PolarWebhookUnknownTypeError,
    PolarWebhookVerificationError,
    validate_event,
)

# Alias polar_sdk for compatibility with polar_sdk references
sys.modules.setdefault("polar_sdk", polar)
sys.modules.setdefault("polar_sdk.webhooks", polar.v2026_10.webhooks)

# Load .env file
_env_path = find_dotenv(usecwd=True)
if not _env_path:
    _env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path and Path(_env_path).exists():
    load_dotenv(_env_path)

logger = logging.getLogger(__name__)

router = APIRouter()

# Single SDK client instance reused across routes
_polar_client: Polar | None = None
_cached_token: str | None = None
_cached_server: str | None = None


def get_polar_client() -> Polar:
    """
    Constructs and returns a single Polar SDK client reused across routes.
    Reads environment from POLAR_SERVER (production or sandbox).
    """
    global _polar_client, _cached_token, _cached_server
    token = os.environ.get("POLAR_ACCESS_TOKEN", "").strip()
    server_env = os.environ.get("POLAR_SERVER", "production").strip()

    if _polar_client is None or token != _cached_token or server_env != _cached_server:
        env: Literal["production", "sandbox"] = (
            "sandbox" if server_env.lower() == "sandbox" else "production"
        )
        _polar_client = Polar(
            access_token=token,
            environment=env,
        )
        _cached_token = token
        _cached_server = server_env

    return _polar_client


@router.get("/checkout", tags=["Polar"])
def checkout(request: Request) -> RedirectResponse:
    """
    Checkout endpoint driven by ?products=<id>.
    Calls Polar checkouts.create and redirects user to returned checkout URL.
    """
    products = request.query_params.getlist("products")
    if not products:
        single = request.query_params.get("products")
        if single:
            products = [single]

    if not products:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing products in query params",
        )

    try:
        client = get_polar_client()
        checkout_session = client.checkouts.create(products=products)
        return RedirectResponse(
            url=checkout_session.url,
            status_code=status.HTTP_302_FOUND,
        )
    except Exception as exc:
        logger.error(f"Failed to create checkout session: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Checkout creation failed: {exc}",
        )


@router.post("/api/webhook/polar", tags=["Polar"])
async def polar_webhook(request: Request) -> Response:
    """
    Polar Webhook receiver.
    Verifies signature against POLAR_WEBHOOK_SECRET before handling events.
    """
    webhook_secret = os.environ.get("POLAR_WEBHOOK_SECRET", "").strip()
    if not webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="POLAR_WEBHOOK_SECRET is not configured",
        )

    raw_body = await request.body()
    headers = dict(request.headers)

    try:
        event = validate_event(raw_body, headers, webhook_secret)
    except PolarWebhookVerificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid webhook signature",
        ) from exc
    except PolarWebhookUnknownTypeError as exc:
        logger.warning(
            f"Ignoring unsupported signed Polar webhook event: {exc.event_type}"
        )
        return Response(status_code=status.HTTP_202_ACCEPTED)
    except PolarWebhookError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook payload",
        ) from exc

    if event.type == "order.paid":
        # TODO: Handle order-paid event (fulfill order, grant software licenses/quotas)
        order = event.data
        logger.info(f"Received order.paid event for order: {getattr(order, 'id', None)}")
    elif event.type == "customer.state_changed":
        # TODO: Handle customer-state-changed event (reconcile entitlements & granted benefits)
        customer_state = event.data
        logger.info(
            f"Received customer.state_changed event for customer: {getattr(customer_state, 'id', None)}"
        )

    return Response(
        content='{"received": true}',
        media_type="application/json",
        status_code=status.HTTP_202_ACCEPTED,
    )

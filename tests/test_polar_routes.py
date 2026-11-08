"""
Unit and Integration Tests for Polar Routes in SafeMotion AI
Tests:
- GET /checkout: query param validation, redirection, error handling
- POST /api/webhook/polar: signature verification, unconfigured secret handling,
  unknown event type acceptance, order.paid & customer.state_changed dispatching.
"""

import base64
import hashlib
import hmac
import json
import math
import os
import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from polar.v2026_10.webhooks import (
    PolarWebhookError,
    PolarWebhookVerificationError,
)

from src.server import app

client = TestClient(app)


def test_checkout_missing_products_param():
    """Verify that GET /checkout without ?products returns 400 Bad Request."""
    response = client.get("/checkout")
    assert response.status_code == 400
    assert "Missing products" in response.json()["detail"]


def test_checkout_successful_redirect():
    """Verify that GET /checkout?products=<id> redirects (302) to Polar checkout URL."""
    mock_checkout = MagicMock()
    mock_checkout.url = "https://polar.sh/checkout/chk_test_abc123"

    with patch("src.polar_routes.get_polar_client") as mock_get_client:
        mock_polar_instance = MagicMock()
        mock_polar_instance.checkouts.create.return_value = mock_checkout
        mock_get_client.return_value = mock_polar_instance

        response = client.get("/checkout?products=prod_test_456", follow_redirects=False)

        assert response.status_code == 302
        assert response.headers["location"] == "https://polar.sh/checkout/chk_test_abc123"
        mock_polar_instance.checkouts.create.assert_called_once_with(
            products=["prod_test_456"]
        )


def test_checkout_multiple_products():
    """Verify that GET /checkout supports multiple product query params."""
    mock_checkout = MagicMock()
    mock_checkout.url = "https://polar.sh/checkout/chk_multi_bundle"

    with patch("src.polar_routes.get_polar_client") as mock_get_client:
        mock_polar_instance = MagicMock()
        mock_polar_instance.checkouts.create.return_value = mock_checkout
        mock_get_client.return_value = mock_polar_instance

        response = client.get("/checkout?products=prod_1&products=prod_2", follow_redirects=False)

        assert response.status_code == 302
        assert response.headers["location"] == "https://polar.sh/checkout/chk_multi_bundle"
        mock_polar_instance.checkouts.create.assert_called_once_with(
            products=["prod_1", "prod_2"]
        )


def test_checkout_creation_api_failure():
    """Verify that GET /checkout handles upstream Polar API failure cleanly."""
    with patch("src.polar_routes.get_polar_client") as mock_get_client:
        mock_polar_instance = MagicMock()
        mock_polar_instance.checkouts.create.side_effect = RuntimeError("Polar API connection timeout")
        mock_get_client.return_value = mock_polar_instance

        response = client.get("/checkout?products=prod_error", follow_redirects=False)

        assert response.status_code == 500
        assert "Checkout creation failed" in response.json()["detail"]


def test_webhook_unconfigured_secret(monkeypatch):
    """Verify that POST /api/webhook/polar returns 500 if secret is missing."""
    monkeypatch.setenv("POLAR_WEBHOOK_SECRET", "")
    response = client.post("/api/webhook/polar", json={"type": "test"})
    assert response.status_code == 500
    assert "POLAR_WEBHOOK_SECRET is not configured" in response.json()["detail"]


def test_webhook_invalid_signature(monkeypatch):
    """Verify that POST /api/webhook/polar returns 403 on invalid webhook signature."""
    monkeypatch.setenv("POLAR_WEBHOOK_SECRET", "whsec_testsecret123")
    headers = {
        "webhook-id": "msg_001",
        "webhook-timestamp": str(math.floor(time.time())),
        "webhook-signature": "v1,invalidsignature==",
    }
    response = client.post(
        "/api/webhook/polar",
        content=b'{"type": "order.paid"}',
        headers=headers,
    )
    assert response.status_code == 403
    assert "Invalid webhook signature" in response.json()["detail"]


def test_webhook_unknown_event_type_handled_gracefully(monkeypatch):
    """
    Verify that an unknown but validly signed event returns 202 Accepted
    so that Polar does not retry unnecessarily.
    """
    secret = "whsec_" + base64.b64encode(b"01234567890123456789012345678901").decode()
    raw_secret = b"01234567890123456789012345678901"
    monkeypatch.setenv("POLAR_WEBHOOK_SECRET", secret)

    now = time.time()
    msg_id = "msg_unknown_01"
    body = json.dumps({"type": "future.custom.event", "data": {}})
    signed_content = f"{msg_id}.{math.floor(now)}.{body}".encode()
    sig = base64.b64encode(hmac.new(raw_secret, signed_content, hashlib.sha256).digest()).decode()

    headers = {
        "webhook-id": msg_id,
        "webhook-timestamp": str(math.floor(now)),
        "webhook-signature": f"v1,{sig}",
    }

    response = client.post(
        "/api/webhook/polar",
        content=body.encode(),
        headers=headers,
    )
    assert response.status_code == 202


def test_webhook_order_paid_event(monkeypatch):
    """Verify handling of order.paid event returns 202 Accepted."""
    monkeypatch.setenv("POLAR_WEBHOOK_SECRET", "whsec_mock_secret")

    mock_event = MagicMock()
    mock_event.type = "order.paid"
    mock_event.data.id = "ord_live_test_123"

    with patch("src.polar_routes.validate_event", return_value=mock_event):
        response = client.post(
            "/api/webhook/polar",
            content=b'{"type": "order.paid"}',
            headers={"webhook-id": "test_id"},
        )
        assert response.status_code == 202
        assert response.json() == {"received": True}


def test_webhook_customer_state_changed_event(monkeypatch):
    """Verify handling of customer.state_changed event returns 202 Accepted."""
    monkeypatch.setenv("POLAR_WEBHOOK_SECRET", "whsec_mock_secret")

    mock_event = MagicMock()
    mock_event.type = "customer.state_changed"
    mock_event.data.id = "cust_live_test_789"

    with patch("src.polar_routes.validate_event", return_value=mock_event):
        response = client.post(
            "/api/webhook/polar",
            content=b'{"type": "customer.state_changed"}',
            headers={"webhook-id": "test_id_2"},
        )
        assert response.status_code == 202
        assert response.json() == {"received": True}


def test_webhook_malformed_payload_error(monkeypatch):
    """Verify that PolarWebhookError results in 400 Bad Request."""
    monkeypatch.setenv("POLAR_WEBHOOK_SECRET", "whsec_mock_secret")

    with patch(
        "src.polar_routes.validate_event",
        side_effect=PolarWebhookError("Malformed JSON"),
    ):
        response = client.post(
            "/api/webhook/polar",
            content=b"not valid json",
            headers={"webhook-id": "test_id_3"},
        )
        assert response.status_code == 400
        assert "Invalid webhook payload" in response.json()["detail"]

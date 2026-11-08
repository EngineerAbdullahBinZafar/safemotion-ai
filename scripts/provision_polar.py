"""
SafeMotion AI — Polar Provisioning & Verification Script
Author: Engineer Abdullah Bin Zafar

Handles Phase 2 step 4, Phase 5, and Phase 6:
- Validates POLAR_ACCESS_TOKEN against https://api.polar.sh/v1/products/?limit=1
- Lists or provisions "Test Product" ($10.00 one-time)
- Registers webhook endpoint if public HTTPS URL is provided
- Creates a 100% discount code for testing
- Generates localhost checkout link
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Literal

import httpx
from dotenv import find_dotenv, load_dotenv, set_key

# Load environment
env_path = find_dotenv(usecwd=True)
if not env_path:
    env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path and Path(env_path).exists():
    load_dotenv(env_path)

from polar.v2026_10 import Polar


def verify_token(token: str) -> bool:
    """Verifies token against GET https://api.polar.sh/v1/products/?limit=1"""
    if not token:
        return False
    try:
        resp = httpx.get(
            "https://api.polar.sh/v1/products/?limit=1",
            headers={"Authorization": f"Bearer {token}"},
            follow_redirects=True,
            timeout=10.0,
        )
        if 200 <= resp.status_code < 300:
            return True
        elif resp.status_code in (401, 403):
            print(
                f"Authentication failed (HTTP {resp.status_code}). "
                "Token must be from production environment with scopes: products, checkouts, webhooks."
            )
            return False
        else:
            print(f"Unexpected status checking token: {resp.status_code}")
            return False
    except Exception as e:
        print(f"Network error verifying token: {e}")
        return False


def provision(public_url: str | None = None) -> dict:
    token = os.environ.get("POLAR_ACCESS_TOKEN", "").strip()
    if not token:
        print("ERROR: POLAR_ACCESS_TOKEN is missing or empty in .env")
        return {"success": False, "error": "missing_token"}

    print("Step 1: Verifying Polar access token...")
    if not verify_token(token):
        return {"success": False, "error": "invalid_token"}
    print("[OK] Polar token verified successfully.")

    server_env = os.environ.get("POLAR_SERVER", "production").strip()
    env: Literal["production", "sandbox"] = (
        "sandbox" if server_env.lower() == "sandbox" else "production"
    )

    client = Polar(access_token=token, environment=env)

    # 1. Products
    print("Step 2: Checking existing products...")
    existing_products = client.products.list(is_archived=False, limit=10)
    product_id = None
    if existing_products.items:
        product_id = existing_products.items[0].id
        product_name = existing_products.items[0].name
        print(f"[OK] Found existing active product: {product_name} (ID: {product_id})")
    else:
        print("Creating Test Product ($10.00 one-time)...")
        created_product = client.products.create(
            name="Test Product",
            description="Test Product for SafeMotion AI Polar checkout integration",
            prices=[
                {
                    "amount_type": "fixed",
                    "price_amount": 1000,
                    "price_currency": "usd",
                }
            ],
        )
        product_id = created_product.id
        print(f"[OK] Created test product: {created_product.name} (ID: {product_id})")

    # 2. Webhooks
    webhook_id = None
    if public_url:
        clean_url = public_url.rstrip("/") + "/api/webhook/polar"
        print(f"Step 3: Checking webhooks for {clean_url}...")
        existing_endpoints = client.webhooks.list_endpoints(limit=10)
        already_registered = False
        for ep in existing_endpoints.items:
            if ep.url == clean_url:
                webhook_id = ep.id
                already_registered = True
                print(f"[OK] Webhook endpoint already exists (ID: {webhook_id})")
                break

        if not already_registered:
            print(f"Registering webhook endpoint at {clean_url}...")
            endpoint = client.webhooks.create_endpoint(
                url=clean_url,
                format="raw",
                events=["order.paid", "customer.state_changed"],
            )
            webhook_id = endpoint.id
            webhook_secret = getattr(endpoint, "secret", None)
            print(f"[OK] Registered webhook endpoint (ID: {webhook_id})")
            if webhook_secret:
                set_key(str(env_path), "POLAR_WEBHOOK_SECRET", webhook_secret)
                print("[OK] Updated POLAR_WEBHOOK_SECRET in .env securely")
    else:
        print("Step 3: Local-only setup (no public URL). Webhook registration deferred to deploy time.")

    # 3. 100% Discount Code for testing
    print("Step 4: Creating/ensuring 100% test discount code...")
    discount_code = "TEST100"
    try:
        discounts = client.discounts.list(limit=10)
        found_discount = any(
            getattr(d, "code", None) == discount_code for d in discounts.items
        )
        if not found_discount:
            client.discounts.create(
                name="100% Testing Discount",
                code=discount_code,
                type="percentage",
                basis_points=10000,
                duration="once",
            )
            print(f"[OK] Created 100% discount code: {discount_code}")
        else:
            print(f"[OK] Test discount code {discount_code} already exists")
    except Exception as e:
        print(f"Note on discount creation: {e}")

    checkout_link = f"http://localhost:8000/checkout?products={product_id}"
    print(f"\n==========================================")
    print(f"Polar Integration Ready!")
    print(f"Checkout Link: {checkout_link}")
    print(f"Use discount code: {discount_code} on checkout to test without real charge.")
    print(f"==========================================")

    return {
        "success": True,
        "product_id": product_id,
        "webhook_id": webhook_id,
        "checkout_link": checkout_link,
        "discount_code": discount_code,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Provision Polar products, webhooks, and discounts")
    parser.add_argument("--public-url", default=None, help="Public HTTPS URL for webhooks")
    args = parser.parse_args()
    provision(args.public_url)

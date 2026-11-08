"""
SafeMotion AI — FastAPI Endpoint Integration Tests
"""

import pytest
from fastapi.testclient import TestClient
from src.server import app

client = TestClient(app)


def test_root_endpoint():
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "online"
    assert "SafeMotion AI" in data["service"]


def test_health_telemetry_endpoint():
    resp = client.get("/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["cbf_solver_latency_us"] > 0
    assert "Forward Invariance" in data["guarantee"]


def test_pricing_endpoint():
    resp = client.get("/v1/pricing")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["tiers"]) == 3
    assert data["payout_channel"] == "Payoneer Direct to United Bank Limited (UBL) Pakistan IBAN"


def test_safety_filter_nominal():
    payload = {
        "robot_state": {"x": 0.0, "y": 0.0, "theta": 0.0},
        "u_ai": {"v": 1.0, "omega": 0.2},
        "obstacles": [],
        "gamma": 1.8,
        "r_min": 0.25,
    }
    resp = client.post("/v1/safety/filter", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_safe"] is True
    assert data["forward_invariant"] is True
    assert data["u_safe"]["v"] == 1.0
    assert data["u_safe"]["omega"] == 0.2
    assert data["attenuation_ratio"] == 1.0


def test_safety_filter_hazard_attenuation():
    # Robot at (0.0, 0.0) driving forward towards obstacle at (0.7, 0.0) with radius 0.25
    payload = {
        "robot_state": {"x": 0.0, "y": 0.0, "theta": 0.0},
        "u_ai": {"v": 1.5, "omega": 0.0},
        "obstacles": [{"x": 0.7, "y": 0.0, "radius": 0.25}],
        "gamma": 1.8,
        "r_min": 0.25,
    }
    resp = client.post("/v1/safety/filter", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    # Safe velocity must be attenuated
    assert data["u_safe"]["v"] < 1.5
    assert data["attenuation_ratio"] < 1.0
    assert data["solver_latency_us"] < 500.0  # sub-millisecond execution


def test_trajectory_verify_endpoint():
    payload = {
        "initial_state": {"x": 0.0, "y": 0.0, "theta": 0.0},
        "waypoints": [
            {"v": 0.5, "omega": 0.0, "duration_s": 0.5},
            {"v": 0.5, "omega": 0.1, "duration_s": 0.5},
        ],
        "obstacles": [
            {"x": 3.0, "y": 0.0, "radius": 0.3},
        ],
        "dt": 0.05,
    }
    resp = client.post("/v1/safety/verify-trajectory", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["certified"] is True
    assert data["collision_detected"] is False
    assert data["min_clearance_meters"] > 1.5

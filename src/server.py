"""
SafeMotion AI — High-Throughput FastAPI Safety Gateway Server
Author: Engineer Abdullah Bin Zafar
"""

import time
from typing import Dict
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .cbf_core import CBFSafetyFilter
from .config import settings
from .models import (
    ControlInput,
    SafetyFilterRequest,
    SafetyFilterResponse,
    TrajectoryVerifyRequest,
    TrajectoryVerifyResponse,
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Sub-millisecond Deterministic Control Barrier Function (CBF-QP) Safety API for Embodied AI and Mobile Robotics.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration for web integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared singleton solver instance
_filter_engine = CBFSafetyFilter(
    v_min=-0.5,
    v_max=settings.MAX_LINEAR_SPEED,
    omega_max=settings.MAX_ANGULAR_SPEED,
    gamma=settings.DEFAULT_GAMMA,
    r_min=settings.DEFAULT_ROBOT_RADIUS,
)


@app.get("/", tags=["General"])
def root() -> Dict[str, str]:
    return {
        "service": settings.PROJECT_NAME,
        "author": settings.AUTHOR,
        "status": "online",
        "documentation": "/docs",
        "mcp_endpoint": "/mcp",
    }


@app.get("/v1/health", tags=["Telemetry"])
def health_check() -> Dict[str, object]:
    # Quick micro-benchmark
    t0 = time.perf_counter_ns()
    res = _filter_engine.filter_control(
        state=(0.0, 0.0, 0.0),
        u_ai=(1.0, 0.0),
        obstacles=[(1.0, 0.0, 0.2)],
    )
    t1 = time.perf_counter_ns()
    benchmark_us = round((t1 - t0) / 1000.0, 2)

    return {
        "status": "healthy",
        "version": settings.VERSION,
        "cbf_solver_latency_us": benchmark_us,
        "guarantee": "Forward Invariance h(x) >= 0 (Nagumo Theorem)",
        "active_profiles": ["unicycle_2d", "differential_drive", "autosar_e2e"],
    }


@app.post("/v1/safety/filter", response_model=SafetyFilterResponse, tags=["Safety Gateway"])
def filter_velocity(req: SafetyFilterRequest) -> SafetyFilterResponse:
    """
    Real-time velocity projection onto the forward-invariant safe set.
    """
    obs_tuples = [(o.x, o.y, o.radius) for o in req.obstacles]
    
    # Configure custom radius/gamma if provided
    engine = _filter_engine
    if req.r_min is not None and req.r_min != engine.r_min:
        engine = CBFSafetyFilter(r_min=req.r_min, gamma=req.gamma or engine.gamma)

    result = engine.filter_control(
        state=(req.robot_state.x, req.robot_state.y, req.robot_state.theta),
        u_ai=(req.u_ai.v, req.u_ai.omega),
        obstacles=obs_tuples,
        gamma=req.gamma,
    )

    u_safe_tuple = result["u_safe"]

    return SafetyFilterResponse(
        is_safe=bool(result["is_safe"]),
        forward_invariant=bool(result["forward_invariant"]),
        u_original=req.u_ai,
        u_safe=ControlInput(v=u_safe_tuple[0], omega=u_safe_tuple[1]),
        attenuation_ratio=float(result["attenuation_ratio"]),
        min_barrier_h=float(result["min_barrier_h"]),
        solver_latency_us=float(result["solver_latency_us"]),
        kkt_slack=float(result["kkt_slack"]),
    )


@app.post("/v1/safety/verify-trajectory", response_model=TrajectoryVerifyResponse, tags=["Safety Gateway"])
def verify_trajectory(req: TrajectoryVerifyRequest) -> TrajectoryVerifyResponse:
    """
    Validates an entire planned waypoint trajectory over time against obstacles.
    """
    waypoints_tuples = [(w.v, w.omega, w.duration_s) for w in req.waypoints]
    obs_tuples = [(o.x, o.y, o.radius) for o in req.obstacles]

    res = _filter_engine.verify_trajectory(
        initial_state=(req.initial_state.x, req.initial_state.y, req.initial_state.theta),
        waypoints=waypoints_tuples,
        obstacles=obs_tuples,
        dt=req.dt,
    )

    return TrajectoryVerifyResponse(
        certified=bool(res["certified"]),
        min_clearance_meters=float(res["min_clearance_meters"]),
        collision_detected=bool(res["collision_detected"]),
        time_to_collision_s=res["time_to_collision_s"],
        trajectory_points_count=int(res["trajectory_points_count"]),
    )


@app.get("/v1/pricing", tags=["Monetization"])
def get_pricing_tiers() -> Dict[str, object]:
    return {
        "tiers": [
            {
                "tier": "Developer Free",
                "price": "$0/month",
                "quota": f"{settings.FREE_TIER_MONTHLY_QUOTA:,} calls/month",
                "features": ["Community Support", "Sub-100µs Local Engine", "REST API Access"],
            },
            {
                "tier": "Pro SaaS",
                "price": f"${settings.PRO_TIER_PRICE_USD}/month",
                "quota": f"{settings.PRO_TIER_MONTHLY_QUOTA:,} calls/month",
                "features": ["Multi-Obstacle CBF-QP", "Priority SLA (<10ms cloud)", "Crash Analytics Dashboard", "MCP SSE Bridge"],
            },
            {
                "tier": "Enterprise Appliance",
                "price": f"${settings.ENTERPRISE_TIER_PRICE_USD} one-time / perpetual license",
                "quota": "Unlimited on-premise execution",
                "features": ["Hardened Docker Container", "AUTOSAR E2E Profile 1 CAN framing", "Dedicated Support", "Source Code Escrow"],
            },
        ],
        "merchant_of_record": "LemonSqueezy / Polar.sh (Global VAT & sales tax handled automatically)",
        "payout_channel": "Automated Global Billing Gateway",
    }

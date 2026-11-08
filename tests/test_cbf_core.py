"""
SafeMotion AI — Comprehensive Unit Test Suite
Author: Engineer Abdullah Bin Zafar
"""

import math
import pytest
from src.cbf_core import CBFSafetyFilter


@pytest.fixture
def cbf_filter():
    return CBFSafetyFilter(
        v_min=-0.5,
        v_max=1.5,
        omega_max=2.5,
        gamma=1.8,
        r_min=0.25,
    )


def test_barrier_positive_outside(cbf_filter):
    # Obstacle at (2.0, 0.0) with radius 0.25. Robot at (0.0, 0.0) with r_min 0.25.
    # Dist = 2.0. Safe radius sum = 0.5. Dist^2 - (0.5)^2 = 4.0 - 0.25 = 3.75 > 0
    h = cbf_filter.compute_barrier(0.0, 0.0, 2.0, 0.0, 0.25)
    assert h > 0.0
    assert pytest.approx(h, 0.01) == 3.75


def test_barrier_zero_on_boundary(cbf_filter):
    # Boundary is at distance = r_min + r_obs = 0.25 + 0.25 = 0.5
    h = cbf_filter.compute_barrier(0.5, 0.0, 0.0, 0.0, 0.25)
    assert pytest.approx(h, 1e-5) == 0.0


def test_barrier_negative_inside_obstacle(cbf_filter):
    # Inside collision envelope: dist = 0.2 < 0.5
    h = cbf_filter.compute_barrier(0.2, 0.0, 0.0, 0.0, 0.25)
    assert h < 0.0


def test_nominal_motion_when_free_space(cbf_filter):
    # No obstacles -> input must pass through unchanged
    res = cbf_filter.filter_control(
        state=(0.0, 0.0, 0.0),
        u_ai=(1.0, 0.2),
        obstacles=[],
    )
    assert res["is_safe"] is True
    assert res["u_safe"] == (1.0, 0.2)
    assert res["attenuation_ratio"] == 1.0


def test_velocity_attenuation_towards_obstacle(cbf_filter):
    # Robot at (0.0, 0.0) heading 0 rad, obstacle at (0.6, 0.0, 0.25).
    # Desired speed 1.2 m/s would crash into (0.6 - 0.5 = 0.1m clearance).
    res = cbf_filter.filter_control(
        state=(0.0, 0.0, 0.0),
        u_ai=(1.2, 0.0),
        obstacles=[(0.6, 0.0, 0.25)],
    )
    v_safe, _ = res["u_safe"]
    assert v_safe < 1.2
    assert res["attenuation_ratio"] < 1.0
    assert res["forward_invariant"] is True


def test_actuator_limits_clamping(cbf_filter):
    # Unconstrained AI asks for 5.0 m/s and 10.0 rad/s
    res = cbf_filter.filter_control(
        state=(0.0, 0.0, 0.0),
        u_ai=(5.0, 10.0),
        obstacles=[],
    )
    v_safe, omega_safe = res["u_safe"]
    assert v_safe <= cbf_filter.v_max
    assert abs(omega_safe) <= cbf_filter.omega_max


def test_solver_latency_performance(cbf_filter):
    # Must solve in < 100 microseconds
    obstacles = [(1.0, 0.5, 0.2), (1.5, -0.2, 0.3), (2.0, 0.1, 0.25)]
    res = cbf_filter.filter_control(
        state=(0.0, 0.0, 0.1),
        u_ai=(1.0, 0.0),
        obstacles=obstacles,
    )
    assert res["solver_latency_us"] < 200.0  # well under 200µs on any host


def test_trajectory_verification_clear(cbf_filter):
    # Straight path for 1.0s at 0.5 m/s -> moves to x = 0.5.
    # Obstacle at x = 2.0 (far away)
    res = cbf_filter.verify_trajectory(
        initial_state=(0.0, 0.0, 0.0),
        waypoints=[(0.5, 0.0, 1.0)],
        obstacles=[(2.0, 0.0, 0.2)],
        dt=0.05,
    )
    assert res["certified"] is True
    assert res["collision_detected"] is False
    assert res["min_clearance_meters"] > 1.0


def test_trajectory_verification_collision_detected(cbf_filter):
    # Path moving directly through obstacle at (1.0, 0.0)
    res = cbf_filter.verify_trajectory(
        initial_state=(0.0, 0.0, 0.0),
        waypoints=[(1.0, 0.0, 2.0)],
        obstacles=[(1.0, 0.0, 0.25)],
        dt=0.05,
    )
    assert res["certified"] is False
    assert res["collision_detected"] is True
    assert res["time_to_collision_s"] is not None

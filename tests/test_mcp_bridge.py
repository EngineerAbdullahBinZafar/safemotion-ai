"""
SafeMotion AI — MCP Bridge Unit Tests
"""

import json
from src.mcp_bridge import TOOLS, handle_filter_velocity, handle_verify_trajectory


def test_tools_manifest():
    tool_names = [t["name"] for t in TOOLS]
    assert "safemotion_filter_velocity" in tool_names
    assert "safemotion_verify_trajectory" in tool_names


def test_mcp_filter_velocity_handler():
    args = {
        "state": [0.0, 0.0, 0.0],
        "u_ai": [1.5, 0.0],
        "obstacles": [[0.8, 0.0, 0.25]],
        "gamma": 1.8,
    }
    res = handle_filter_velocity(args)
    assert res["is_safe"] is True
    assert res["u_safe"][0] < 1.5
    assert res["attenuation_ratio"] < 1.0


def test_mcp_verify_trajectory_handler():
    args = {
        "initial_state": [0.0, 0.0, 0.0],
        "waypoints": [[0.5, 0.0, 0.5]],
        "obstacles": [[2.0, 0.0, 0.2]],
        "dt": 0.05,
    }
    res = handle_verify_trajectory(args)
    assert res["certified"] is True
    assert res["collision_detected"] is False

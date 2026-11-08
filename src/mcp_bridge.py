"""
SafeMotion AI — Model Context Protocol (MCP) Server Bridge
Exposes real-time CBF-QP safety tools to Claude Desktop, Antigravity, and AI Agents.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, List
from .cbf_core import CBFSafetyFilter

solver = CBFSafetyFilter()


def handle_filter_velocity(arguments: Dict[str, Any]) -> Dict[str, Any]:
    state = arguments.get("state", [0.0, 0.0, 0.0])
    u_ai = arguments.get("u_ai", [0.0, 0.0])
    obstacles = arguments.get("obstacles", [])

    obs_tuples = [(o[0], o[1], o[2]) for o in obstacles]
    res = solver.filter_control(
        state=(float(state[0]), float(state[1]), float(state[2])),
        u_ai=(float(u_ai[0]), float(u_ai[1])),
        obstacles=obs_tuples,
        gamma=float(arguments.get("gamma", 1.8)),
    )
    return res


def handle_verify_trajectory(arguments: Dict[str, Any]) -> Dict[str, Any]:
    init_state = arguments.get("initial_state", [0.0, 0.0, 0.0])
    waypoints = arguments.get("waypoints", [])
    obstacles = arguments.get("obstacles", [])

    wp_tuples = [(float(w[0]), float(w[1]), float(w[2]) if len(w) > 2 else 0.5) for w in waypoints]
    obs_tuples = [(float(o[0]), float(o[1]), float(o[2])) for o in obstacles]

    res = solver.verify_trajectory(
        initial_state=(float(init_state[0]), float(init_state[1]), float(init_state[2])),
        waypoints=wp_tuples,
        obstacles=obs_tuples,
        dt=float(arguments.get("dt", 0.05)),
    )
    return res


TOOLS = [
    {
        "name": "safemotion_filter_velocity",
        "description": "Applies Control Barrier Function (CBF-QP) safety filter to proposed linear and angular velocity commands (v, omega) to guarantee collision-free forward invariance.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "state": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "[x, y, theta] current robot pose in meters and radians",
                },
                "u_ai": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "[v, omega] proposed control input in m/s and rad/s",
                },
                "obstacles": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "[x, y, radius] of obstacle",
                    },
                    "description": "List of obstacles in world frame",
                },
                "gamma": {
                    "type": "number",
                    "description": "Barrier conservatism parameter (default 1.8)",
                },
            },
            "required": ["state", "u_ai"],
        },
    },
    {
        "name": "safemotion_verify_trajectory",
        "description": "Validates a multi-step forward waypoint trajectory against obstacles, returning minimum clearance and collision prediction.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "initial_state": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "[x, y, theta] start state",
                },
                "waypoints": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {"type": "number"},
                    },
                    "description": "List of [v, omega, duration] control steps",
                },
                "obstacles": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {"type": "number"},
                    },
                    "description": "List of [x, y, radius] obstacles",
                },
            },
            "required": ["initial_state", "waypoints"],
        },
    },
]


def run_stdio_server() -> None:
    """Standard IO JSON-RPC 2.0 loop for MCP protocol."""
    sys.stdout.reconfigure(encoding="utf-8")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})

            if method == "tools/list":
                resp = {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
            elif method == "tools/call":
                tool_name = params.get("name")
                args = params.get("arguments", {})
                if tool_name == "safemotion_filter_velocity":
                    res = handle_filter_velocity(args)
                elif tool_name == "safemotion_verify_trajectory":
                    res = handle_verify_trajectory(args)
                else:
                    res = {"error": f"Unknown tool: {tool_name}"}
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(res, indent=2)}]},
                }
            elif method == "initialize":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "safemotion-ai-mcp", "version": "1.0.0"},
                    },
                }
            else:
                resp = {"jsonrpc": "2.0", "id": req_id, "result": {}}

            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
        except Exception as e:
            err_resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": str(e)}}
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    run_stdio_server()

"""
SafeMotion AI — Pydantic Schemas & Data Contracts
"""

from __future__ import annotations

from typing import List, Optional, Tuple
from pydantic import BaseModel, Field


class RobotState(BaseModel):
    x: float = Field(..., description="X coordinate in world frame (meters)")
    y: float = Field(..., description="Y coordinate in world frame (meters)")
    theta: float = Field(..., description="Heading orientation angle in radians")


class ControlInput(BaseModel):
    v: float = Field(..., description="Linear velocity in m/s")
    omega: float = Field(..., description="Angular velocity in rad/s")


class Obstacle(BaseModel):
    x: float = Field(..., description="Obstacle X coordinate (meters)")
    y: float = Field(..., description="Obstacle Y coordinate (meters)")
    radius: float = Field(0.25, description="Obstacle safety envelope radius (meters)")


class SafetyFilterRequest(BaseModel):
    robot_state: RobotState
    u_ai: ControlInput = Field(..., description="Raw unconstrained command proposed by AI/LLM")
    obstacles: List[Obstacle] = Field(default_factory=list, description="Surrounding detected obstacles")
    gamma: Optional[float] = Field(1.8, description="Class-K barrier conservatism parameter")
    r_min: Optional[float] = Field(0.25, description="Robot bounding collision radius (meters)")


class SafetyFilterResponse(BaseModel):
    is_safe: bool = Field(..., description="True if state is currently outside unsafe set")
    forward_invariant: bool = Field(..., description="True if invariant set is strictly maintained")
    u_original: ControlInput
    u_safe: ControlInput = Field(..., description="Certified safe control vector")
    attenuation_ratio: float = Field(..., description="Ratio of safe velocity to AI requested velocity")
    min_barrier_h: float = Field(..., description="Signed distance certificate: h(x) >= 0 implies safety")
    solver_latency_us: float = Field(..., description="QP solver computation time in microseconds")
    kkt_slack: float = Field(..., description="KKT active constraint slack metric")


class TrajectoryWaypoint(BaseModel):
    v: float
    omega: float
    duration_s: float = Field(0.5, description="Duration to execute this command (seconds)")


class TrajectoryVerifyRequest(BaseModel):
    initial_state: RobotState
    waypoints: List[TrajectoryWaypoint]
    obstacles: List[Obstacle]
    dt: float = Field(0.05, description="Simulation discrete integration step size")


class TrajectoryVerifyResponse(BaseModel):
    certified: bool = Field(..., description="True if no collision occurred along entire horizon")
    min_clearance_meters: float
    collision_detected: bool
    time_to_collision_s: Optional[float]
    trajectory_points_count: int

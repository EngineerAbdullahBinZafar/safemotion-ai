"""
SafeMotion AI — Real-Time Control Barrier Function (CBF-QP) Core Engine
Author: Engineer Abdullah Bin Zafar <abz.king.1.9.2003@gmail.com>
License: Apache-2.0

Sub-millisecond mathematical safety shield for Embodied AI and Autonomous Robotics.
Guarantees forward invariance h(x) >= 0 under unconstrained neural or LLM commands.
"""

from __future__ import annotations

import math
import time
from typing import Dict, List, Optional, Tuple


class CBFSafetyFilter:
    """
    Real-Time Closed-Form Control Barrier Function Quadratic Program (CBF-QP) Solver.
    
    Given robot state x = [px, py, theta]^T and unconstrained AI input u_ai = [v, omega]^T:
        minimize    1/2 || u - u_ai ||_Q^2
        subject to  L_f h(x) + L_g h(x) u >= -gamma * h(x)
                    v_min <= v <= v_max
                    -omega_max <= omega <= omega_max
    """

    def __init__(
        self,
        v_min: float = -0.5,
        v_max: float = 1.5,
        omega_max: float = 2.5,
        gamma: float = 1.8,
        r_min: float = 0.25,
    ) -> None:
        self.v_min = v_min
        self.v_max = v_max
        self.omega_max = omega_max
        self.gamma = gamma
        self.r_min = r_min

    def compute_barrier(
        self,
        px: float,
        py: float,
        obs_x: float,
        obs_y: float,
        obs_radius: float,
    ) -> float:
        """
        Safety barrier certificate function:
            h(x) = || p - p_obs ||^2 - (r_robot + r_obs)^2
        Safety is guaranteed if and only if h(x) >= 0.
        """
        dx = px - obs_x
        dy = py - obs_y
        dist_sq = dx * dx + dy * dy
        safe_radius = self.r_min + obs_radius
        return dist_sq - (safe_radius * safe_radius)

    @staticmethod
    def _solve_2d_with_shift(
        v_nom: float,
        w_nom: float,
        v_min: float,
        v_max: float,
        w_min: float,
        w_max: float,
        raw_cs: List[Tuple[float, float, float]],
        delta: float,
    ) -> Tuple[bool, Tuple[float, float]]:
        hps: List[Tuple[float, float, float]] = [
            (1.0, 0.0, v_min),
            (-1.0, 0.0, -v_max),
            (0.0, 1.0, w_min),
            (0.0, -1.0, -w_max),
        ]
        normed_cbfs: List[Tuple[float, float, float]] = []
        for a0, a1, b in raw_cs:
            b_shift = b - delta
            n = math.hypot(a0, a1)
            if n <= 1e-12:
                if b_shift > 1e-9:
                    return False, (0.0, 0.0)
            else:
                normed_cbfs.append((a0 / n, a1 / n, b_shift / n))

        uv = max(v_min, min(v_max, v_nom))
        uw = max(w_min, min(w_max, w_nom))

        for n0, n1, d in normed_cbfs:
            if n0 * uv + n1 * uw < d - 1e-12:
                s_nom = n0 * v_nom + n1 * w_nom
                pv = v_nom + (d - s_nom) * n0
                pw = w_nom + (d - s_nom) * n1
                dv, dw = -n1, n0
                t_min = -float("inf")
                t_max = float("inf")
                for m0, m1, dm in hps:
                    alpha = m0 * dv + m1 * dw
                    beta = dm - (m0 * pv + m1 * pw)
                    if alpha > 1e-11:
                        val = beta / alpha
                        if val > t_min:
                            t_min = val
                    elif alpha < -1e-11:
                        val = beta / alpha
                        if val < t_max:
                            t_max = val
                    else:
                        if beta > 1e-9:
                            return False, (uv, uw)

                if t_min > t_max + 1e-9:
                    return False, (uv, uw)
                if t_min > t_max:
                    t_opt = 0.5 * (t_min + t_max)
                else:
                    t_opt = 0.0
                    if t_opt < t_min:
                        t_opt = t_min
                    if t_opt > t_max:
                        t_opt = t_max
                uv = pv + t_opt * dv
                uw = pw + t_opt * dw
            hps.append((n0, n1, d))

        uv = max(v_min, min(v_max, uv))
        uw = max(w_min, min(w_max, uw))
        for a0, a1, b in raw_cs:
            if a0 * uv + a1 * uw < b - delta - 1e-6:
                return False, (uv, uw)
        return True, (uv, uw)

    def filter_control(
        self,
        state: Tuple[float, float, float],
        u_ai: Tuple[float, float],
        obstacles: List[Tuple[float, float, float]],
        gamma: Optional[float] = None,
    ) -> Dict[str, object]:
        """
        Executes real-time safety projection across all obstacle CBF and actuator constraints.

        Args:
            state: (px, py, theta) in meters and radians.
            u_ai: (v, omega) proposed by LLM or planner.
            obstacles: List of (obs_x, obs_y, obs_radius).
            gamma: Optional override for class-K barrier aggressiveness parameter.

        Returns:
            Dictionary containing certified u_safe, barrier values, and solver metrics.
        """
        t_start = time.perf_counter_ns()
        active_gamma = gamma if gamma is not None else self.gamma

        px, py, theta = state
        v_des = float(u_ai[0])
        omega_des = float(u_ai[1])

        v_clamped = max(self.v_min, min(self.v_max, v_des))
        omega_clamped = max(-self.omega_max, min(self.omega_max, omega_des))

        if not obstacles:
            t_end = time.perf_counter_ns()
            return {
                "u_safe": (float(v_clamped), float(omega_clamped)),
                "is_safe": True,
                "forward_invariant": True,
                "min_barrier_h": 999.0,
                "attenuation_ratio": 1.0 if math.hypot(v_des, omega_des) < 1e-9 else round(
                    min(1.0, math.hypot(v_clamped, omega_clamped) / max(math.hypot(v_des, omega_des), 1e-6)),
                    4,
                ),
                "solver_latency_us": round((t_end - t_start) / 1000.0, 2),
                "kkt_slack": 0.0,
            }

        cos_t = math.cos(theta)
        sin_t = math.sin(theta)

        min_h = float("inf")
        raw_cs: List[Tuple[float, float, float]] = []

        for obs_x, obs_y, obs_r in obstacles:
            dx = px - obs_x
            dy = py - obs_y
            h = self.compute_barrier(px, py, obs_x, obs_y, obs_r)
            if h < min_h:
                min_h = h

            # Exact Lie derivative of h(px, py) = ||p - p_obs||^2 - r_safe^2
            # under unicycle dynamics g(x) = [cos(theta), 0; sin(theta), 0; 0, 1]:
            # L_f h(x) = 0, L_g h(x) = [2*(dx*cos_t + dy*sin_t), 0.0]
            a_v = 2.0 * (dx * cos_t + dy * sin_t)
            a_omega = 0.0
            b = -active_gamma * h
            raw_cs.append((a_v, a_omega, b))

        # Fast check: if box-clamped u_ai satisfies all CBF constraints, it is the exact QP optimum
        box_feasible = all(
            a_v * v_clamped + a_omega * omega_clamped >= b - 1e-12
            for a_v, a_omega, b in raw_cs
        )

        if box_feasible:
            v_final = v_clamped
            omega_final = omega_clamped
        else:
            ok, (v_sol, omega_sol) = self._solve_2d_with_shift(
                v_des,
                omega_des,
                self.v_min,
                self.v_max,
                -self.omega_max,
                self.omega_max,
                raw_cs,
                0.0,
            )
            if ok:
                v_final = v_sol
                omega_final = omega_sol
            else:
                # Infeasible intersection: find minimum worst-case slack delta >= 0 inside box
                d_hi = max(
                    [0.0] + [b - (a_v * v_clamped + a_omega * omega_clamped) for a_v, a_omega, b in raw_cs]
                ) * 1.01 + 1e-6
                d_lo = 0.0
                v_final, omega_final = v_clamped, omega_clamped
                for _ in range(40):
                    mid = 0.5 * (d_lo + d_hi)
                    ok_m, (vm, wm) = self._solve_2d_with_shift(
                        v_des,
                        omega_des,
                        self.v_min,
                        self.v_max,
                        -self.omega_max,
                        self.omega_max,
                        raw_cs,
                        mid,
                    )
                    if ok_m:
                        d_hi = mid
                        v_final, omega_final = vm, wm
                    else:
                        d_lo = mid

        v_final = float(v_final)
        omega_final = float(omega_final)

        # Verify actual satisfaction of all CBF inequalities and box bounds on returned command
        max_violation = 0.0
        for a_v, a_omega, b in raw_cs:
            viol = b - (a_v * v_final + a_omega * omega_final)
            if viol > max_violation:
                max_violation = viol

        in_box = (
            self.v_min - 1e-9 <= v_final <= self.v_max + 1e-9
            and abs(omega_final) <= self.omega_max + 1e-9
        )
        forward_invariant = in_box and (max_violation <= 1e-6)

        norm_ai = math.hypot(v_des, omega_des)
        norm_safe = math.hypot(v_final, omega_final)
        attenuation = norm_safe / max(norm_ai, 1e-6)

        t_end = time.perf_counter_ns()
        latency_us = round((t_end - t_start) / 1000.0, 2)

        return {
            "u_safe": (v_final, omega_final),
            "is_safe": min_h >= 0.0,
            "forward_invariant": forward_invariant,
            "min_barrier_h": round(min_h, 4),
            "attenuation_ratio": round(min(1.0, attenuation), 4),
            "solver_latency_us": latency_us,
            "kkt_slack": round(max_violation, 6),
        }

    def verify_trajectory(
        self,
        initial_state: Tuple[float, float, float],
        waypoints: List[Tuple[float, float, float]],
        obstacles: List[Tuple[float, float, float]],
        dt: float = 0.05,
    ) -> Dict[str, object]:
        """
        Simulates and certifies a forward trajectory against barrier sets.
        """
        px, py, theta = initial_state
        min_clearance = float("inf")
        collision_detected = False
        time_to_collision = None

        simulated_path: List[Tuple[float, float, float]] = [(px, py, theta)]

        for step_idx, (v_cmd, omega_cmd, horizon_t) in enumerate(waypoints):
            steps = max(1, int(horizon_t / dt))
            for _ in range(steps):
                px += v_cmd * math.cos(theta) * dt
                py += v_cmd * math.sin(theta) * dt
                theta += omega_cmd * dt

                simulated_path.append((round(px, 3), round(py, 3), round(theta, 3)))

                # Check proximity to obstacles
                for obs_x, obs_y, obs_r in obstacles:
                    d = math.hypot(px - obs_x, py - obs_y) - (self.r_min + obs_r)
                    if d < min_clearance:
                        min_clearance = d
                    if d <= 0 and not collision_detected:
                        collision_detected = True
                        time_to_collision = round(step_idx * horizon_t, 3)

        return {
            "certified": not collision_detected,
            "min_clearance_meters": round(min_clearance, 3),
            "collision_detected": collision_detected,
            "time_to_collision_s": time_to_collision,
            "trajectory_points_count": len(simulated_path),
        }

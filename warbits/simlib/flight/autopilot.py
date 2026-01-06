from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, Optional

import numpy as np

from ..math3d import safe_unit
from .kinematics import signed_angle_2d
from .types import FlightLimits, Waypoint, WaypointNavigator

Vec3 = np.ndarray


@dataclass(frozen=True)
class L1Config:
    """Config for the L1 lateral guidance primitive.

    L1 guidance is a classic “lightweight autopilot” approach that turns toward
    a waypoint (or a path segment) with a smooth, speed-dependent turn command.

    We’re using a simplified version tuned for deterministic gameplay / sim.
    """

    period_s: float = 20.0        # larger = gentler turns
    damping: float = 0.75         # typical ~0.7–0.9
    min_distance_m: float = 50.0  # prevents division blowups at low speed

    def l1_distance_m(self, speed_mps: float) -> float:
        # A common relationship: L1 distance proportional to speed and period.
        # This is not “the one true formula” — it’s a stable, deterministic choice.
        v = max(float(speed_mps), 0.0)
        base = (v * self.period_s) / (2.0 * math.pi)
        return float(max(self.min_distance_m, base) * self.damping)


@dataclass
class AutopilotCommand:
    """Autopilot output (renderer-agnostic)."""

    target_speed_mps: float
    target_direction_unit: Vec3  # unit vector
    debug: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        d = safe_unit(self.target_direction_unit)
        object.__setattr__(self, "target_direction_unit", d)


@dataclass
class L1Autopilot:
    """A minimal deterministic waypoint-following autopilot.

    Inputs:
    - current position and velocity
    - current target waypoint (or navigator)
    - flight limits (stall/min speed, max turn rate, climb limits)

    Output:
    - desired velocity direction + desired speed

    You can then run the output through `limit_velocity_vector()` to enforce the
    same limits in the final authority layer (recommended).
    """

    cruise_speed_mps: float = 220.0
    altitude_gain: float = 0.05  # (1/s) vertical response gain
    l1: L1Config = field(default_factory=L1Config)

    def update(
        self,
        position_m: Vec3,
        velocity_mps: Vec3,
        waypoint: Waypoint,
        limits: FlightLimits,
        dt_s: float,
    ) -> AutopilotCommand:
        dt = float(dt_s)
        if dt <= 0:
            raise ValueError("dt_s must be > 0")

        pos = np.asarray(position_m, dtype=float)
        vel = np.asarray(velocity_mps, dtype=float)
        if pos.shape != (3,) or vel.shape != (3,):
            raise ValueError("position_m and velocity_mps must be shape (3,).")

        speed = float(np.linalg.norm(vel))
        # Desired speed: waypoint override -> autopilot cruise -> limits caps
        desired_speed = float(waypoint.desired_speed_mps) if waypoint.desired_speed_mps is not None else float(self.cruise_speed_mps)
        desired_speed = max(desired_speed, limits.min_speed_mps)
        if limits.max_speed_mps is not None:
            desired_speed = min(desired_speed, float(limits.max_speed_mps))

        # Lateral (XY) guidance toward the waypoint
        to_wp = waypoint.position_m - pos
        to_wp_xy = np.array([to_wp[0], to_wp[1]], dtype=float)
        dist_xy = float(np.linalg.norm(to_wp_xy))

        vel_xy = np.array([vel[0], vel[1]], dtype=float)
        speed_xy = float(np.linalg.norm(vel_xy))

        # Pick a current forward direction in XY
        if speed_xy > 1e-6:
            vhat_xy = vel_xy / speed_xy
        else:
            # Standing still: point directly at waypoint (or +X fallback)
            if dist_xy > 1e-6:
                vhat_xy = to_wp_xy / dist_xy
            else:
                vhat_xy = np.array([1.0, 0.0], dtype=float)

        # Desired direction to waypoint in XY
        if dist_xy > 1e-6:
            dir_to_wp_xy = to_wp_xy / dist_xy
        else:
            dir_to_wp_xy = vhat_xy

        # L1 “lookahead”
        l1_dist = self.l1.l1_distance_m(max(speed_xy, 1.0))
        # Angle between current velocity direction and line-of-sight to waypoint
        eta = signed_angle_2d(vhat_xy, dir_to_wp_xy)

        # Lateral accel command (m/s^2)
        a_lat = 2.0 * (max(speed_xy, 1.0) ** 2) / max(l1_dist, 1e-6) * math.sin(eta)
        # Convert to bank angle request
        bank_cmd = math.atan2(a_lat, 9.80665)
        # Clamp to limits
        bank_cmd = float(max(-limits.max_bank_rad, min(limits.max_bank_rad, bank_cmd)))

        # Convert bank to a desired heading update for this dt.
        # omega = g * tan(phi) / V
        omega = 9.80665 * math.tan(bank_cmd) / max(speed_xy, 1.0)
        dpsi = omega * dt

        # Apply heading change in XY
        c = math.cos(dpsi)
        s = math.sin(dpsi)
        new_vhat_xy = np.array([c * vhat_xy[0] - s * vhat_xy[1], s * vhat_xy[0] + c * vhat_xy[1]], dtype=float)
        new_vhat_xy = new_vhat_xy / max(float(np.linalg.norm(new_vhat_xy)), 1e-12)

        # Vertical guidance: simple P controller on altitude error into a vz request.
        alt_err = float(waypoint.position_m[2] - pos[2])
        vz_cmd = alt_err * float(self.altitude_gain) * desired_speed  # scale by speed for “stronger response” at higher speed

        if limits.max_climb_rate_mps is not None:
            vz_cmd = min(vz_cmd, float(limits.max_climb_rate_mps))
        if limits.max_descent_rate_mps is not None:
            vz_cmd = max(vz_cmd, -float(limits.max_descent_rate_mps))

        # Build a 3D direction vector that respects vz_cmd while keeping total speed = desired_speed.
        vz = float(vz_cmd)
        horiz = math.sqrt(max(desired_speed * desired_speed - vz * vz, 0.0))
        dir3 = np.array([new_vhat_xy[0] * horiz, new_vhat_xy[1] * horiz, vz], dtype=float)
        dir3_unit = safe_unit(dir3)

        debug: Dict[str, float] = {
            "speed_xy": speed_xy,
            "dist_xy": dist_xy,
            "eta_rad": float(eta),
            "l1_dist": float(l1_dist),
            "a_lat": float(a_lat),
            "bank_cmd_rad": float(bank_cmd),
            "omega_rad_s": float(omega),
            "dpsi_rad": float(dpsi),
            "alt_err_m": float(alt_err),
            "vz_cmd": float(vz_cmd),
        }
        return AutopilotCommand(target_speed_mps=float(desired_speed), target_direction_unit=dir3_unit, debug=debug)

    def update_navigator(
        self,
        position_m: Vec3,
        velocity_mps: Vec3,
        navigator: WaypointNavigator,
        limits: FlightLimits,
        dt_s: float,
    ) -> AutopilotCommand:
        """Convenience: advance navigator if reached, then update on current waypoint."""
        navigator.advance_if_reached(position_m)
        return self.update(position_m, velocity_mps, navigator.current(), limits, dt_s)

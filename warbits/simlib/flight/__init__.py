"""warbits.simlib.flight

Flight primitives for WarBits.

This package is intentionally **not** a full-blown 6-DOF flight dynamics model.
The goal is to make the sim *more realistic and more consistent* (turn limits,
climb limits, stall limits) without torching your frame-time budget.

What you get here:
- A small aircraft performance spec model (typed, unit-annotated).
- A `compute_flight_limits()` helper that turns partial data into usable limits.
- A `limit_velocity_vector()` helper you can drop in front of scripted flight plans.
- An L1-style autopilot primitive for following waypoints deterministically.

These modules are renderer-agnostic and safe to import in headless mode.
"""

from .types import AircraftPerformance, FlightLimits, Waypoint, WaypointNavigator
from .envelope import compute_flight_limits, stall_speed_mps, coordinated_turn_rate_rad_s
from .limiter import limit_velocity_vector
from .autopilot import L1Autopilot, AutopilotCommand, L1Config

__all__ = [
    "AircraftPerformance",
    "FlightLimits",
    "Waypoint",
    "WaypointNavigator",
    "compute_flight_limits",
    "stall_speed_mps",
    "coordinated_turn_rate_rad_s",
    "limit_velocity_vector",
    "L1Autopilot",
    "AutopilotCommand",
    "L1Config",
]

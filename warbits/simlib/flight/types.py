from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence

import numpy as np

Vec3 = np.ndarray


@dataclass(frozen=True)
class AircraftPerformance:
    """Aircraft performance inputs for envelope/limiting/autopilot logic.

    This is meant to be *data-store friendly*: you can create it from vehicles.json,
    hand-authored scenario data, or a small test fixture.

    All units are SI.
    """

    # Optional aero/performance data (real aircraft data is messy — allow partial).
    mass_kg: Optional[float] = None
    wing_area_m2: Optional[float] = None
    cl_max: Optional[float] = None  # max lift coefficient before stall
    cd0: Optional[float] = None     # parasite drag coefficient (optional)
    k_induced: Optional[float] = None  # induced drag factor (optional)

    max_thrust_N: Optional[float] = None
    max_speed_mps: Optional[float] = None

    max_climb_rate_mps: Optional[float] = None  # +Z
    max_descent_rate_mps: Optional[float] = None  # magnitude, positive number

    max_accel_mps2: Optional[float] = None  # longitudinal accel cap for limiter

    # Structural/handling limits (these are *always* meaningful, even with partial aero data).
    max_g: float = 8.0
    max_bank_deg: float = 70.0

    # Optional direct overrides (useful if you have hard caps from a dataset).
    stall_speed_mps: Optional[float] = None
    min_speed_mps: Optional[float] = None  # if set, overrides stall/min computation
    max_turn_rate_rad_s: Optional[float] = None  # global turn-rate cap override

    # Small human notes (debugging/provenance, not used for math).
    label: str = ""

    def validate(self, *, strict: bool = False) -> None:
        """Validate obvious invariants.

        If strict=True, missing fields that prevent computing a stall speed will raise.
        """
        if self.mass_kg is not None and self.mass_kg <= 0:
            raise ValueError(f"mass_kg must be > 0, got {self.mass_kg}")
        if self.wing_area_m2 is not None and self.wing_area_m2 <= 0:
            raise ValueError(f"wing_area_m2 must be > 0, got {self.wing_area_m2}")
        if self.cl_max is not None and self.cl_max <= 0:
            raise ValueError(f"cl_max must be > 0, got {self.cl_max}")
        if self.max_g <= 1.0:
            raise ValueError(f"max_g must be > 1.0, got {self.max_g}")
        if not (0.0 <= self.max_bank_deg <= 89.9):
            raise ValueError(f"max_bank_deg should be within [0, 89.9], got {self.max_bank_deg}")
        if self.max_speed_mps is not None and self.max_speed_mps <= 0:
            raise ValueError(f"max_speed_mps must be > 0, got {self.max_speed_mps}")
        if self.stall_speed_mps is not None and self.stall_speed_mps < 0:
            raise ValueError(f"stall_speed_mps must be >= 0, got {self.stall_speed_mps}")
        if self.min_speed_mps is not None and self.min_speed_mps < 0:
            raise ValueError(f"min_speed_mps must be >= 0, got {self.min_speed_mps}")
        if self.max_accel_mps2 is not None and self.max_accel_mps2 <= 0:
            raise ValueError(f"max_accel_mps2 must be > 0, got {self.max_accel_mps2}")
        if strict:
            # Strict mode requires enough data to compute at least a min speed.
            has_min = self.min_speed_mps is not None or self.stall_speed_mps is not None
            has_formula = self.mass_kg is not None and self.wing_area_m2 is not None and self.cl_max is not None
            if not (has_min or has_formula):
                raise ValueError(
                    "Strict mode requires either min_speed_mps/stall_speed_mps or mass_kg+wing_area_m2+cl_max."
                )


@dataclass(frozen=True)
class FlightLimits:
    """Derived flight limits used by limiters/autopilot.

    This is the “runtime ready” version of AircraftPerformance for a given air density.
    """

    min_speed_mps: float
    max_speed_mps: Optional[float]

    max_g: float
    max_bank_rad: float  # used for coordinated turn limits

    # Optional climb/descent limits (None means “unbounded”).
    max_climb_rate_mps: Optional[float] = None
    max_descent_rate_mps: Optional[float] = None  # magnitude (positive)

    # Optional longitudinal accel cap (m/s^2).
    max_accel_mps2: Optional[float] = None

    # Optional hard cap on turn rate (rad/s).
    max_turn_rate_rad_s: Optional[float] = None

    # Bookkeeping
    rho_kg_m3: float = 1.225
    stall_speed_mps: Optional[float] = None
    label: str = ""

    def turn_rate_limit_rad_s(self, speed_mps: float) -> float:
        """Max *coordinated* turn rate at this speed, clamped by any override.

        Formula: omega = g * tan(bank) / V

        Notes:
        - This is a **kinematic** cap used for “don’t cheat” limiting.
        - It is not a full aerodynamic sustained-turn solver.
        """
        from .envelope import coordinated_turn_rate_rad_s  # local import to avoid cycles

        v = max(float(speed_mps), 1e-6)
        omega = coordinated_turn_rate_rad_s(v, self.max_bank_rad)
        if self.max_turn_rate_rad_s is not None:
            omega = min(omega, float(self.max_turn_rate_rad_s))
        return omega


@dataclass(frozen=True)
class Waypoint:
    """A single waypoint in 3D space."""

    position_m: Vec3
    acceptance_radius_m: float = 100.0
    desired_speed_mps: Optional[float] = None  # if None, autopilot uses its cruise speed

    def __post_init__(self) -> None:
        p = np.asarray(self.position_m, dtype=float)
        if p.shape != (3,):
            raise ValueError(f"Waypoint.position_m must be shape (3,), got {p.shape}")
        object.__setattr__(self, "position_m", p)
        if self.acceptance_radius_m < 0:
            raise ValueError("acceptance_radius_m must be >= 0")


@dataclass
class WaypointNavigator:
    """Deterministic waypoint sequencer.

    You give it a list of waypoints. It hands you the current one, and you call
    `advance_if_reached()` each tick.

    This is intentionally tiny and predictable.
    """

    waypoints: Sequence[Waypoint]
    loop: bool = True
    index: int = 0

    def __post_init__(self) -> None:
        if len(self.waypoints) == 0:
            raise ValueError("WaypointNavigator requires at least 1 waypoint.")

    def current(self) -> Waypoint:
        return self.waypoints[self.index]

    def advance_if_reached(self, position_m: Vec3) -> bool:
        """Advance to the next waypoint if current is reached.

        Returns True if we advanced, False otherwise.
        """
        wp = self.current()
        d = float(np.linalg.norm(np.asarray(position_m, dtype=float) - wp.position_m))
        if d <= wp.acceptance_radius_m:
            if self.index + 1 < len(self.waypoints):
                self.index += 1
            elif self.loop:
                self.index = 0
            # If not looping and we’re at the last WP, we stay pinned there.
            return True
        return False

    def is_final(self) -> bool:
        return (not self.loop) and (self.index == len(self.waypoints) - 1)

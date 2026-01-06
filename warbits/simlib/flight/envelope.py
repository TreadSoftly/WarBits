from __future__ import annotations

import math
from typing import Optional

from .types import AircraftPerformance, FlightLimits


def stall_speed_mps(
    mass_kg: float,
    wing_area_m2: float,
    cl_max: float,
    rho_kg_m3: float,
    *,
    g_mps2: float = 9.80665,
) -> float:
    """Compute stall speed using a basic lift equation.

    Vstall = sqrt( (2 * W) / (rho * S * CLmax) )

    This is a simplified estimate, but it’s a *good* lever for realism:
    - heavier aircraft stall faster
    - higher altitude (lower rho) increases stall speed
    - bigger wing / higher CLmax reduces stall speed

    Returns speed in m/s.
    """
    if mass_kg <= 0:
        raise ValueError("mass_kg must be > 0")
    if wing_area_m2 <= 0:
        raise ValueError("wing_area_m2 must be > 0")
    if cl_max <= 0:
        raise ValueError("cl_max must be > 0")
    if rho_kg_m3 <= 0:
        raise ValueError("rho_kg_m3 must be > 0")

    w = mass_kg * g_mps2
    v2 = (2.0 * w) / (rho_kg_m3 * wing_area_m2 * cl_max)
    return float(math.sqrt(max(v2, 0.0)))


def max_bank_for_load_factor_rad(max_g: float) -> float:
    """Max bank angle (rad) that can be sustained in a level coordinated turn at max_g."""
    if max_g <= 1.0:
        return 0.0
    # n = 1 / cos(phi) -> cos(phi) = 1/n
    inv = 1.0 / float(max_g)
    inv = min(max(inv, -1.0), 1.0)
    return float(math.acos(inv))


def coordinated_turn_rate_rad_s(speed_mps: float, bank_rad: float, *, g_mps2: float = 9.80665) -> float:
    """Coordinated turn rate omega (rad/s) for a given speed and bank angle.

    omega = g * tan(phi) / V

    This is the standard “bank-to-turn” relationship for coordinated turns.
    """
    v = float(speed_mps)
    if v <= 0:
        return 0.0
    return float(g_mps2 * math.tan(float(bank_rad)) / v)


def compute_flight_limits(
    perf: AircraftPerformance,
    *,
    rho_kg_m3: float = 1.225,
    strict: bool = False,
    g_mps2: float = 9.80665,
    stall_margin: float = 1.15,
) -> FlightLimits:
    """Turn an AircraftPerformance into runtime limits for a specific air density.

    - `rho_kg_m3` should come from your atmosphere model at the aircraft altitude.
    - `stall_margin` inflates stall speed into a “minimum safe speed” (typical 1.1–1.3).

    If strict=True:
    - missing inputs that prevent computing a usable min_speed will raise.

    Returns a FlightLimits object that can be fed into:
    - limit_velocity_vector()
    - L1Autopilot
    """
    perf.validate(strict=strict)

    # Stall/min speed
    stall: Optional[float] = None
    if perf.min_speed_mps is not None:
        min_speed = float(perf.min_speed_mps)
    else:
        if perf.stall_speed_mps is not None:
            stall = float(perf.stall_speed_mps)
        elif (perf.mass_kg is not None) and (perf.wing_area_m2 is not None) and (perf.cl_max is not None):
            stall = stall_speed_mps(float(perf.mass_kg), float(perf.wing_area_m2), float(perf.cl_max), float(rho_kg_m3), g_mps2=g_mps2)
        elif strict:
            raise ValueError("Cannot compute stall/min speed in strict mode.")
        else:
            # Unknown: allow flight model to run, but don’t pretend it’s realistic.
            stall = None

        if stall is None:
            min_speed = 0.0
        else:
            min_speed = float(stall * float(stall_margin))

    # Bank / g limit: ensure bank isn’t implying >max_g in sustained level turn
    bank_from_g = max_bank_for_load_factor_rad(perf.max_g)
    bank_from_setting = math.radians(float(perf.max_bank_deg))
    max_bank_rad = float(min(bank_from_setting, bank_from_g))

    # Sanity clamp: avoid 90-degree tan explosions
    max_bank_rad = float(min(max_bank_rad, math.radians(89.0)))

    return FlightLimits(
        min_speed_mps=float(max(0.0, min_speed)),
        max_speed_mps=None if perf.max_speed_mps is None else float(perf.max_speed_mps),
        max_g=float(perf.max_g),
        max_bank_rad=max_bank_rad,
        max_climb_rate_mps=None if perf.max_climb_rate_mps is None else float(perf.max_climb_rate_mps),
        max_descent_rate_mps=None if perf.max_descent_rate_mps is None else float(perf.max_descent_rate_mps),
        max_accel_mps2=None if perf.max_accel_mps2 is None else float(perf.max_accel_mps2),
        max_turn_rate_rad_s=None if perf.max_turn_rate_rad_s is None else float(perf.max_turn_rate_rad_s),
        rho_kg_m3=float(rho_kg_m3),
        stall_speed_mps=stall,
        label=perf.label,
    )

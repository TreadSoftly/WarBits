"""Aerodynamic helper functions (drag-focused).

These are intentionally generic so they can be reused by:
- bullets
- rockets
- bombs
- parachutes
- future flight models (lift/drag)

This is not a full aero model. It's a clean place to put the basics.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import numpy.typing as npt

from .math3d import safe_unit

ArrayLike = float | npt.NDArray[np.floating[Any]]
Array = npt.NDArray[np.float64]


def dynamic_pressure_pa(rho_kg_m3: ArrayLike, speed_mps: ArrayLike) -> Array:
    """q = 1/2 rho V^2"""
    rho = np.asarray(rho_kg_m3, dtype=float)
    v = np.asarray(speed_mps, dtype=float)
    return 0.5 * rho * v * v


def drag_force_n(
    rho_kg_m3: ArrayLike,
    v_rel_mps: npt.NDArray[np.floating[Any]],
    cd_area_m2: float,
) -> Array:
    """Compute drag force vector (N) opposing v_rel."""
    v_rel = np.asarray(v_rel_mps, dtype=float)
    speed = np.linalg.norm(v_rel, axis=-1)
    q = dynamic_pressure_pa(rho_kg_m3, speed)
    mag = q * cd_area_m2  # (..,)
    dirn = -safe_unit(v_rel)
    # Broadcast mag to vector shape
    return dirn * mag[..., None]


def drag_accel_mps2(
    rho_kg_m3: ArrayLike,
    v_rel_mps: npt.NDArray[np.floating[Any]],
    mass_kg: float,
    cd_area_m2: float,
) -> Array:
    """Compute drag acceleration vector (m/s^2)."""
    if mass_kg <= 0:
        raise ValueError("mass_kg must be positive")
    return drag_force_n(rho_kg_m3, v_rel_mps, cd_area_m2) / float(mass_kg)


def ballistic_coefficient_kg_m2(mass_kg: float, cd: float, area_m2: float) -> float:
    """BC = m / (Cd * A). Higher BC -> less drag."""
    if cd <= 0 or area_m2 <= 0:
        raise ValueError("cd and area must be positive")
    return float(mass_kg) / (float(cd) * float(area_m2))


def cd_area_from_bc(mass_kg: float, bc_kg_m2: float) -> float:
    """Return Cd*A from mass and ballistic coefficient."""
    if bc_kg_m2 <= 0:
        raise ValueError("bc_kg_m2 must be positive")
    return float(mass_kg) / float(bc_kg_m2)

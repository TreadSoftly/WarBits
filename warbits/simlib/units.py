"""Unit conversion + sanity checking helpers.

Rule: SI internally.
This module exists so ingestion + UI glue code can convert external units
into SI once, at the boundary.

This is not a full unit algebra system (by design).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Iterable, Optional

from .errors import DeterminismError


# Length
FT_TO_M: float = 0.3048
NM_TO_M: float = 1852.0

# Speed
KNOT_TO_MPS: float = 0.5144444444444445  # exact: 1852/3600
MPH_TO_MPS: float = 0.44704

# Mass
LB_TO_KG: float = 0.45359237

# Angles
DEG_TO_RAD: float = math.pi / 180.0
RAD_TO_DEG: float = 180.0 / math.pi

# Acceleration (g)
G_TO_MPS2: float = 9.80665


def ft_to_m(x_ft: float) -> float:
    return x_ft * FT_TO_M


def m_to_ft(x_m: float) -> float:
    return x_m / FT_TO_M


def nm_to_m(x_nm: float) -> float:
    return x_nm * NM_TO_M


def m_to_nm(x_m: float) -> float:
    return x_m / NM_TO_M


def knots_to_mps(x_kt: float) -> float:
    return x_kt * KNOT_TO_MPS


def mps_to_knots(x_mps: float) -> float:
    return x_mps / KNOT_TO_MPS


def mph_to_mps(x_mph: float) -> float:
    return x_mph * MPH_TO_MPS


def mps_to_mph(x_mps: float) -> float:
    return x_mps / MPH_TO_MPS


def lb_to_kg(x_lb: float) -> float:
    return x_lb * LB_TO_KG


def kg_to_lb(x_kg: float) -> float:
    return x_kg / LB_TO_KG


def deg_to_rad(x_deg: float) -> float:
    return x_deg * DEG_TO_RAD


def rad_to_deg(x_rad: float) -> float:
    return x_rad * RAD_TO_DEG


def g_to_mps2(x_g: float) -> float:
    return x_g * G_TO_MPS2


def mps2_to_g(x_mps2: float) -> float:
    return x_mps2 / G_TO_MPS2


def require_finite(name: str, value: float) -> float:
    """Raise if value is NaN/inf. Returns value for chaining."""
    if not math.isfinite(value):
        raise DeterminismError(f"{name} must be finite, got {value!r}")
    return value


def require_vec_finite(name: str, vec: Iterable[float]) -> None:
    for i, v in enumerate(vec):
        if not math.isfinite(float(v)):
            raise DeterminismError(f"{name}[{i}] must be finite, got {v!r}")

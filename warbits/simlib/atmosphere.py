"""International Standard Atmosphere (ISA) helper functions.

This is a lightweight atmosphere model sufficient for:
- density-based drag
- speed of sound approximations (optional)
- pressure/temperature for future aero models

We implement a simple ISA:
- Troposphere (0..11 km) with linear lapse rate
- Lower stratosphere (11..20 km) isothermal

Beyond 20 km we clamp at 20 km by default (configurable).

References:
- Standard ISA equations (widely published). We avoid using any proprietary tables.

All outputs are SI units.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import numpy.typing as npt

from .constants import (
    G0_MPS2,
    GAMMA_AIR,
    ISA_LAPSE_K_PER_M,
    ISA_P0_PA,
    ISA_RHO0_KG_M3,
    ISA_STRATOSPHERE_END_M,
    ISA_T0_K,
    ISA_TROPOPAUSE_M,
    R_AIR_J_PER_KG_K,
)


ArrayLike = float | npt.NDArray[np.floating[Any]]
Array = npt.NDArray[np.float64]


def _as_array(x: ArrayLike) -> Array:
    return np.asarray(x, dtype=float)


def isa_temperature_k(alt_m: ArrayLike, *, clamp: bool = True) -> Array:
    """Temperature in Kelvin at altitude."""
    h = _as_array(alt_m)
    if clamp:
        h = np.clip(h, -1000.0, ISA_STRATOSPHERE_END_M)
    # Troposphere
    t_trop = ISA_T0_K - ISA_LAPSE_K_PER_M * h
    # Stratosphere: constant temperature at tropopause
    t11 = ISA_T0_K - ISA_LAPSE_K_PER_M * ISA_TROPOPAUSE_M
    return np.where(h <= ISA_TROPOPAUSE_M, t_trop, t11)


def isa_pressure_pa(alt_m: ArrayLike, *, clamp: bool = True) -> Array:
    """Static pressure in Pa at altitude."""
    h = _as_array(alt_m)
    if clamp:
        h = np.clip(h, -1000.0, ISA_STRATOSPHERE_END_M)

    L = ISA_LAPSE_K_PER_M
    T0 = ISA_T0_K
    P0 = ISA_P0_PA
    R = R_AIR_J_PER_KG_K
    g = G0_MPS2

    # Troposphere formula
    T = T0 - L * h
    expo = g / (R * L)
    P_trop = P0 * (T / T0) ** expo

    # Values at 11 km
    T11 = T0 - L * ISA_TROPOPAUSE_M
    P11 = P0 * (T11 / T0) ** expo

    # Stratosphere: isothermal
    P_strat = P11 * np.exp(-g * (h - ISA_TROPOPAUSE_M) / (R * T11))

    return np.where(h <= ISA_TROPOPAUSE_M, P_trop, P_strat)


def isa_density_kg_m3(alt_m: ArrayLike, *, clamp: bool = True) -> Array:
    """Air density in kg/m^3 at altitude."""
    T = isa_temperature_k(alt_m, clamp=clamp)
    P = isa_pressure_pa(alt_m, clamp=clamp)
    return P / (R_AIR_J_PER_KG_K * T)


def isa_speed_of_sound_mps(alt_m: ArrayLike, *, clamp: bool = True) -> Array:
    """Speed of sound in m/s at altitude."""
    T = isa_temperature_k(alt_m, clamp=clamp)
    return np.sqrt(GAMMA_AIR * R_AIR_J_PER_KG_K * T)


def isa_properties(alt_m: ArrayLike, *, clamp: bool = True) -> tuple[Array, Array, Array, Array]:
    """Return (T[K], P[Pa], rho[kg/m^3], a[m/s])."""
    T = isa_temperature_k(alt_m, clamp=clamp)
    P = isa_pressure_pa(alt_m, clamp=clamp)
    rho = P / (R_AIR_J_PER_KG_K * T)
    a = np.sqrt(GAMMA_AIR * R_AIR_J_PER_KG_K * T)
    return T, P, rho, a


def density_ratio(alt_m: ArrayLike) -> Array:
    """rho(alt)/rho0"""
    return isa_density_kg_m3(alt_m) / ISA_RHO0_KG_M3

"""WarBits simlib: reusable building blocks for realism + determinism.

This package is intentionally renderer-agnostic and safe to import in headless mode.
"""

from __future__ import annotations

from .errors import WarBitsError, PhysicsError, StrictPhysicsError, DataError, DeterminismError, ConfigError, ErrorContext
from .rng import DeterministicRNG, stable_seed_u64
from .units import (
    ft_to_m,
    m_to_ft,
    nm_to_m,
    m_to_nm,
    knots_to_mps,
    mps_to_knots,
    mph_to_mps,
    mps_to_mph,
    lb_to_kg,
    kg_to_lb,
    deg_to_rad,
    rad_to_deg,
    g_to_mps2,
    mps2_to_g,
    require_finite,
)
from .math3d import (
    clamp,
    norm,
    norm2,
    unit,
    safe_unit,
    clamp_vec_norm,
    angle_between,
    wrap_angle_rad,
    wrap_angle_deg,
)
from .integrators import IntegratorConfig, integrate_step
from .atmosphere import isa_density_kg_m3, isa_pressure_pa, isa_temperature_k, isa_speed_of_sound_mps, isa_properties
from .aero import dynamic_pressure_pa, drag_force_n, drag_accel_mps2, ballistic_coefficient_kg_m2, cd_area_from_bc
from . import flight as flight

__all__ = [
    "WarBitsError",
    "PhysicsError",
    "StrictPhysicsError",
    "DataError",
    "DeterminismError",
    "ConfigError",
    "ErrorContext",
    "DeterministicRNG",
    "stable_seed_u64",
    "ft_to_m",
    "m_to_ft",
    "nm_to_m",
    "m_to_nm",
    "knots_to_mps",
    "mps_to_knots",
    "mph_to_mps",
    "mps_to_mph",
    "lb_to_kg",
    "kg_to_lb",
    "deg_to_rad",
    "rad_to_deg",
    "g_to_mps2",
    "mps2_to_g",
    "require_finite",
    "clamp",
    "norm",
    "norm2",
    "unit",
    "safe_unit",
    "clamp_vec_norm",
    "angle_between",
    "wrap_angle_rad",
    "wrap_angle_deg",
    "IntegratorConfig",
    "integrate_step",
    "isa_density_kg_m3",
    "isa_pressure_pa",
    "isa_temperature_k",
    "isa_speed_of_sound_mps",
    "isa_properties",
    "dynamic_pressure_pa",
    "drag_force_n",
    "drag_accel_mps2",
    "ballistic_coefficient_kg_m2",
    "cd_area_from_bc",
    "flight",
]

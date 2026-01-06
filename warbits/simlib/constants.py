"""Physical constants and standard atmosphere reference values.

All values are SI units unless explicitly stated.
"""

from __future__ import annotations

# Gravitational acceleration at sea level (standard gravity)
G0_MPS2: float = 9.80665  # m/s^2

# Universal gas constant / molar mass for dry air -> specific gas constant for air
R_AIR_J_PER_KG_K: float = 287.05287  # J/(kg*K) for dry air

# Ratio of specific heats (gamma) for air (approx)
GAMMA_AIR: float = 1.4

# ISA sea-level conditions
ISA_T0_K: float = 288.15  # K
ISA_P0_PA: float = 101_325.0  # Pa
ISA_RHO0_KG_M3: float = 1.225  # kg/m^3

# ISA tropospheric lapse rate (0-11 km)
ISA_LAPSE_K_PER_M: float = 0.0065  # K/m

# ISA tropopause altitude
ISA_TROPOPAUSE_M: float = 11_000.0  # m
ISA_STRATOSPHERE_END_M: float = 20_000.0  # m (lower stratosphere model ends here)

# Small epsilons used across numeric kernels
EPS: float = 1e-12
EPS_NORM: float = 1e-9

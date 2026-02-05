"""Damage modeling utilities (starter kit).

This module is designed to be:
- deterministic
- data-driven (warhead explosive mass, penetration, etc.)
- cheap (no heavy physics engine)

It does NOT pretend to be a perfect real-world model. The goal is:
- consistent behavior
- tunable parameters
- clear extension points for more realism later

Core concept:
- Platforms have components with health.
- Explosions apply damage based on distance and explosive mass (cube-root scaling).
- Direct impacts can apply component-specific damage (later).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, TypeAlias

import numpy as np
from numpy.typing import NDArray

FloatArray: TypeAlias = NDArray[np.float64]


@dataclass(frozen=True)
class ComponentSpec:
    component_id: str
    max_health: float = 100.0
    critical: bool = False  # if destroyed, platform is considered mission-killed
    armor_factor: float = 1.0  # >1 means tougher; <1 means fragile


@dataclass
class ComponentState:
    spec: ComponentSpec
    health: float = field(init=False)

    def __post_init__(self) -> None:
        self.health = float(self.spec.max_health)

    @property
    def destroyed(self) -> bool:
        return self.health <= 0.0

    def apply_damage(self, dmg: float) -> None:
        if dmg <= 0.0 or self.destroyed:
            return
        self.health = float(max(0.0, self.health - dmg))


@dataclass
class PlatformDamageState:
    platform_id: str
    components: Dict[str, ComponentState]

    @classmethod
    def from_specs(cls, platform_id: str, specs: Iterable[ComponentSpec]) -> "PlatformDamageState":
        comps = {s.component_id: ComponentState(s) for s in specs}
        return cls(platform_id=str(platform_id), components=comps)

    @property
    def mission_killed(self) -> bool:
        # Mission kill if any critical component destroyed.
        return any(c.spec.critical and c.destroyed for c in self.components.values())

    def total_health_fraction(self) -> float:
        max_total = sum(c.spec.max_health for c in self.components.values()) or 1.0
        cur_total = sum(c.health for c in self.components.values())
        return float(cur_total / max_total)


@dataclass(frozen=True)
class BlastModelParams:
    """Tuning knobs for blast damage.

    We use cube-root scaling: characteristic radius ~ k * W^(1/3)
    where W is explosive mass (kg TNT equivalent).

    damage_at_zero: damage multiplier at R=0 relative to component max_health.
    falloff_power: how quickly damage decays with distance.
    """

    k_radius_m_per_kg_cuberoot: float = 8.0
    damage_at_zero: float = 1.0
    falloff_power: float = 2.0
    min_damage_fraction: float = 0.0


def scaled_distance_m_per_kg_cuberoot(distance_m: float, explosive_mass_kg: float) -> float:
    """Hopkinson-Cranz scaled distance Z = R / W^(1/3)."""
    R = float(max(0.0, distance_m))
    W = float(max(0.0, explosive_mass_kg))
    if W <= 0.0:
        return float("inf")
    return R / (W ** (1.0 / 3.0))


def blast_damage_fraction(
    distance_m: float, explosive_mass_kg: float, *, params: BlastModelParams = BlastModelParams()
) -> float:
    """Compute a 0..1 damage fraction based on distance and explosive mass.

    This is a *starter* model:
    - radius scales with cube-root of explosive mass
    - damage decays as (1 - (R/R0)^p) clamped to 0..1
    """
    W = float(max(0.0, explosive_mass_kg))
    if W <= 0.0:
        return 0.0

    R = float(max(0.0, distance_m))
    R0 = float(params.k_radius_m_per_kg_cuberoot) * (W ** (1.0 / 3.0))
    if R0 <= 1e-9:
        return 0.0

    x = R / R0
    # Smooth-ish falloff; at x>=1 damage is near zero
    frac = float(params.damage_at_zero) * max(0.0, 1.0 - (x ** float(params.falloff_power)))
    frac = max(float(params.min_damage_fraction), frac)
    return float(min(1.0, frac))


def apply_blast_to_platform(
    damage_state: PlatformDamageState,
    *,
    platform_pos: FloatArray,
    explosion_pos: FloatArray,
    explosive_mass_kg: float,
    params: BlastModelParams = BlastModelParams(),
) -> Dict[str, float]:
    """Apply blast damage to all components.

    Returns a dict {component_id: damage_applied}.
    """
    p = np.asarray(platform_pos, dtype=float)
    e = np.asarray(explosion_pos, dtype=float)
    d = float(np.linalg.norm(p - e))
    frac = blast_damage_fraction(d, explosive_mass_kg, params=params)

    applied: Dict[str, float] = {}
    for cid, comp in damage_state.components.items():
        if comp.destroyed:
            applied[cid] = 0.0
            continue
        # Armor factor reduces damage.
        armor = float(max(1e-6, comp.spec.armor_factor))
        dmg = frac * float(comp.spec.max_health) / armor
        comp.apply_damage(dmg)
        applied[cid] = float(dmg)

    return applied

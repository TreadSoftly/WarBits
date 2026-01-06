"""
Public re-exports for *warbits.physics*.

Flight-path helpers live in **warbits.logic.flight_paths**; they are
re-exported here for legacy callers.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

# DDDDDDDDDDDDDDDDDDDDDDD Flight paths (re-export) DDDDDDDDDDDDDDDDDDDDDDDDD
from ..logic.flight_paths import generate_path, build_flight_plan, DEFAULT_PHASES

# DDDDDDDDDDDDDDDDDDDDDDD Kinematic kernels DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD
from .ballistics import clamp_xyz_arrays, simulate_bullet_trajectory
from .rockets import simulate_rocket_trajectory
from .bombs import (
    simulate_bomb_trajectory,
    schedule_release as bombs_schedule_release,
    reset as bombs_reset,
    step as bombs_step,
)

# DDDDDDDDDDDDDDDDDDDDDDD Terrain DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD
from .terrain import generate_terrain, draw_terrain

if TYPE_CHECKING:
    from .explosions import register_axes as register_explosion_axes, spawn_explosion, update_explosion
    from .parachute import (
        register_axes as register_parachute_axes,
        spawn_parachute,
        update_parachute,
        reset_parachute,
    )

_LAZY_EXPORTS = {
    "register_explosion_axes": "warbits.physics.explosions",
    "spawn_explosion": "warbits.physics.explosions",
    "update_explosion": "warbits.physics.explosions",
    "register_parachute_axes": "warbits.physics.parachute",
    "spawn_parachute": "warbits.physics.parachute",
    "update_parachute": "warbits.physics.parachute",
    "reset_parachute": "warbits.physics.parachute",
}


def __getattr__(name: str) -> object:
    module_path = _LAZY_EXPORTS.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = __import__(module_path, fromlist=[name])
    value = getattr(module, name)
    globals()[name] = value
    return value


__all__: list[str] = [
    # flight-paths
    "generate_path",
    "build_flight_plan",
    "DEFAULT_PHASES",
    # ballistics / rockets / bombs
    "clamp_xyz_arrays",
    "simulate_bullet_trajectory",
    "simulate_rocket_trajectory",
    "simulate_bomb_trajectory",
    # bomb scene-helpers
    "bombs_schedule_release",
    "bombs_reset",
    "bombs_step",
    # explosions
    "register_explosion_axes",
    "spawn_explosion",
    "update_explosion",
    # parachutes
    "register_parachute_axes",
    "spawn_parachute",
    "update_parachute",
    "reset_parachute",
    # terrain
    "generate_terrain",
    "draw_terrain",
]

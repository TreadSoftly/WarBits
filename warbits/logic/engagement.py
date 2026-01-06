# warbits/scene/engagement.py
from __future__ import annotations

import numpy as np
import numpy.typing as npt

from ..physics.ballistics import (
    simulate_bullet_trajectory,
)
from ..physics.rockets   import simulate_rocket_trajectory
from ..physics.bombs     import simulate_bomb_trajectory
from .state import RUNTIME, Vector3

_F64Arr = npt.NDArray[np.float64]
_DEFAULT_RNG = np.random.default_rng(0)

# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _repeat(v: tuple[float, float, float], n: int) -> _F64Arr:
    return np.repeat(np.asarray(v, dtype=np.float64)[None, :], n, axis=0)

# --------------------------------------------------------------------------- #
# BULLETS
# --------------------------------------------------------------------------- #
def spawn_burst(
    plane_pos: Vector3,
    plane_vel: Vector3,
    *,
    bullets: int = 1,
    muzzle_speed: float = 11_200.0,
    rng: np.random.Generator | None = None,
) -> None:
    if bullets <= 0:
        return
    if rng is None:
        rng = _DEFAULT_RNG

    pos = _repeat(plane_pos, bullets)
    vel = _repeat(plane_vel, bullets)

    # Tiny random spread so bursts don't look laser-precise
    ang = np.deg2rad(2.0)
    speed = np.linalg.norm(vel, axis=1, keepdims=True)
    direction = np.where(speed < 1e-6, np.array([[1.0, 0.0, 0.0]]), vel / speed)
    direction += rng.normal(0.0, ang, size=vel.shape)
    direction /= np.linalg.norm(direction, axis=1, keepdims=True)
    vel = direction * np.maximum(speed, 1e-6)

    x, y, z = simulate_bullet_trajectory(pos, vel, muzzle_speed=muzzle_speed)
    RUNTIME.active_bullets.add(
        x.astype(np.float32), y.astype(np.float32), z.astype(np.float32)
    )

# Legacy monolith wrapper – kept for import-compat
def spawn_bullets(
    px: float,
    py: float,
    pz: float,
    vx: float,
    vy: float,
    vz: float,
    *,
    num_bullets: int = 1,
    muzzle_speed: float = 11_200.0,
    rng: np.random.Generator | None = None,
) -> None:
    spawn_burst(
        (px, py, pz),
        (vx, vy, vz),
        bullets=num_bullets,
        muzzle_speed=muzzle_speed,
        rng=rng,
    )

# --------------------------------------------------------------------------- #
# ROCKETS
# --------------------------------------------------------------------------- #
def spawn_rocket() -> None:
    flt = RUNTIME.flight
    pos = _repeat(flt.plane_pos, 1)
    vel = _repeat(flt.plane_vel, 1)

    x, y, z = simulate_rocket_trajectory(pos, vel)
    RUNTIME.active_rockets.add(
        x.astype(np.float32), y.astype(np.float32), z.astype(np.float32)
    )

# --------------------------------------------------------------------------- #
# BOMBS
# --------------------------------------------------------------------------- #
def spawn_bomb() -> None:
    flt = RUNTIME.flight
    pos = _repeat(flt.plane_pos, 1)
    vel = _repeat(flt.plane_vel, 1)

    x, y, z = simulate_bomb_trajectory(pos, vel)
    RUNTIME.active_bombs.add(
        x.astype(np.float32), y.astype(np.float32), z.astype(np.float32)
    )

# --------------------------------------------------------------------------- #
# PER-TICK UPDATE
# --------------------------------------------------------------------------- #
def step_projectiles() -> None:
    RUNTIME.active_bullets.step()
    RUNTIME.active_rockets.step()
    RUNTIME.active_bombs.step()

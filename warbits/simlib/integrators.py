"""Numerical integrators for simulation.

This module intentionally provides small, testable building blocks.

Design goals:
- Deterministic given same inputs (no hidden RNG).
- Works with numpy vectors.
- Avoids fancy dependencies (no SciPy requirement).

Note:
Real-time sims often use semi-implicit Euler (a.k.a. symplectic Euler)
because it's stable and cheap. RK4 is more accurate but more expensive.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Tuple

import numpy as np
import numpy.typing as npt


Vec = npt.NDArray[np.floating[Any]]


def euler_step(pos: Vec, vel: Vec, accel: Vec, dt: float) -> Tuple[Vec, Vec]:
    """Explicit Euler: pos_{n+1} = pos_n + vel_n dt."""
    pos_n1 = pos + vel * dt
    vel_n1 = vel + accel * dt
    return pos_n1, vel_n1


def semi_implicit_euler_step(pos: Vec, vel: Vec, accel: Vec, dt: float) -> Tuple[Vec, Vec]:
    """Semi-implicit Euler (symplectic): vel first, then pos."""
    vel_n1 = vel + accel * dt
    pos_n1 = pos + vel_n1 * dt
    return pos_n1, vel_n1


def rk4_step(y: Vec, t: float, dt: float, dydt: Callable[[float, Vec], Vec]) -> Vec:
    """Runge-Kutta 4th order step for y' = f(t, y)."""
    k1 = dydt(t, y)
    k2 = dydt(t + 0.5 * dt, y + 0.5 * dt * k1)
    k3 = dydt(t + 0.5 * dt, y + 0.5 * dt * k2)
    k4 = dydt(t + dt, y + dt * k3)
    return y + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)


def rk4_step_second_order(
    pos: Vec,
    vel: Vec,
    t: float,
    dt: float,
    accel_fn: Callable[[float, Vec, Vec], Vec],
) -> Tuple[Vec, Vec]:
    """RK4 for second-order system: pos' = vel, vel' = accel_fn(t, pos, vel)."""
    # State y = [pos, vel]
    y0 = np.concatenate([pos, vel], axis=0)

    def f(tt: float, y: Vec) -> Vec:
        p = y[:3]
        v = y[3:]
        a = accel_fn(tt, p, v)
        return np.concatenate([v, a], axis=0)

    y1 = rk4_step(y0, t, dt, f)
    return y1[:3], y1[3:]


@dataclass(frozen=True)
class IntegratorConfig:
    method: str = "semi_implicit"  # "euler" | "semi_implicit" | "rk4"

    def validate(self) -> None:
        if self.method not in {"euler", "semi_implicit", "rk4"}:
            raise ValueError(f"Unknown integrator method: {self.method}")


def integrate_step(
    pos: Vec,
    vel: Vec,
    accel: Vec,
    t: float,
    dt: float,
    *,
    config: IntegratorConfig | None = None,
    accel_fn: Callable[[float, Vec, Vec], Vec] | None = None,
) -> Tuple[Vec, Vec]:
    """Generic one-step integration helper.

    - If you already have accel computed, pass accel and use euler/semi-implicit.
    - If you want RK4, pass accel_fn to compute acceleration during sub-steps.

    Args:
        pos, vel: (3,) vectors
        accel: (3,) vector (ignored for rk4 when accel_fn provided)
        t: current time
        dt: step size
    """
    cfg = config or IntegratorConfig()
    cfg.validate()

    if cfg.method == "euler":
        return euler_step(pos, vel, accel, dt)
    if cfg.method == "semi_implicit":
        return semi_implicit_euler_step(pos, vel, accel, dt)
    if cfg.method == "rk4":
        if accel_fn is None:
            # Fallback: treat accel as constant across dt (still better than crashing)
            def af(tt: float, p: Vec, v: Vec) -> Vec:
                return accel
            accel_fn = af
        return rk4_step_second_order(pos, vel, t, dt, accel_fn)

    raise AssertionError("unreachable")

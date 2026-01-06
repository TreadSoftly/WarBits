from __future__ import annotations

import dataclasses
from typing import Optional

import numpy as np


@dataclasses.dataclass
class AlphaBetaFilter:
    """Constant-velocity alpha-beta filter for 3D position measurements.

    This is deliberately lightweight (no matrix algebra), but extremely useful for:
    - smoothing noisy observations
    - producing a velocity estimate for intercept/lead calculations
    - deterministic and fast

    Update equations:
      x_pred = x + v*dt
      r = z - x_pred
      x = x_pred + alpha*r
      v = v + (beta/dt)*r

    Typical values:
      alpha ~ 0.6 .. 0.9
      beta  ~ 0.05 .. 0.2
    """

    alpha: float = 0.7
    beta: float = 0.1
    x_m: np.ndarray = dataclasses.field(default_factory=lambda: np.zeros(3, dtype=np.float64))
    v_mps: np.ndarray = dataclasses.field(default_factory=lambda: np.zeros(3, dtype=np.float64))
    initialized: bool = False

    def reset(self) -> None:
        self.x_m = np.zeros(3, dtype=np.float64)
        self.v_mps = np.zeros(3, dtype=np.float64)
        self.initialized = False

    def predict(self, dt_s: float) -> None:
        dt = float(dt_s)
        if not self.initialized:
            return
        self.x_m = self.x_m + self.v_mps * dt

    def update(self, z_m: np.ndarray, dt_s: float) -> None:
        z = np.asarray(z_m, dtype=np.float64).reshape(3)
        dt = float(dt_s)
        if dt <= 1e-9:
            dt = 1e-9

        if not self.initialized:
            self.x_m = z.copy()
            self.v_mps = np.zeros(3, dtype=np.float64)
            self.initialized = True
            return

        x_pred = self.x_m + self.v_mps * dt
        r = z - x_pred
        a = float(self.alpha)
        b = float(self.beta)

        self.x_m = x_pred + a * r
        self.v_mps = self.v_mps + (b / dt) * r

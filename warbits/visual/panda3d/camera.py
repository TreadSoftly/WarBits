"""warbits.visual.panda3d.camera

High-FPS camera controllers for Panda3D.

We treat the camera like a *control system*:
- Compute a desired camera pose from target position/velocity
- Smooth with time-constant smoothing (stable across FPS)
- Avoid per-frame allocations

This module is safe to import without Panda3D installed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np

from .imports import require_panda3d


@dataclass(frozen=True)
class ChaseCameraConfig:
    """Chase camera tuning.

    distance: how far behind target (meters)
    height: how far above target (meters)
    look_ahead: how far in front of target to look (meters)
    smoothing_tau: time constant (seconds). Lower = snappier, higher = smoother.
    min_speed_for_forward: if target speed is below this, forward defaults to +X.
    """

    distance: float = 80.0
    height: float = 22.0
    look_ahead: float = 28.0
    smoothing_tau: float = 0.18
    min_speed_for_forward: float = 2.0


def _safe_unit(v: np.ndarray, eps: float = 1e-9, fallback: np.ndarray | None = None) -> np.ndarray:
    n = float(np.linalg.norm(v))
    if n < eps:
        return (fallback if fallback is not None else np.array([1.0, 0.0, 0.0], dtype=np.float32)).astype(np.float32)
    return (v / n).astype(np.float32)


def compute_chase_camera_pose(
    target_pos: np.ndarray,
    target_vel: np.ndarray,
    *,
    up: np.ndarray = np.array([0.0, 0.0, 1.0], dtype=np.float32),
    cfg: ChaseCameraConfig = ChaseCameraConfig(),
) -> tuple[np.ndarray, np.ndarray]:
    """Compute desired camera position + look-at point (pure math).

    Returns (cam_pos, look_at), both float32 vectors length-3.
    """
    target_pos = np.asarray(target_pos, dtype=np.float32)
    target_vel = np.asarray(target_vel, dtype=np.float32)
    up = _safe_unit(np.asarray(up, dtype=np.float32), fallback=np.array([0.0, 0.0, 1.0], dtype=np.float32))

    speed = float(np.linalg.norm(target_vel))
    forward = _safe_unit(
        target_vel if speed >= cfg.min_speed_for_forward else np.array([1.0, 0.0, 0.0], dtype=np.float32),
        fallback=np.array([1.0, 0.0, 0.0], dtype=np.float32),
    )

    # Camera behind + above.
    cam_pos = target_pos - forward * float(cfg.distance) + up * float(cfg.height)
    look_at = target_pos + forward * float(cfg.look_ahead)
    return cam_pos.astype(np.float32), look_at.astype(np.float32)


class ChaseCameraController:
    """A chase camera that follows a moving target.

    Usage:
        ctrl = ChaseCameraController(base.camera)
        ctrl.update(dt, target_pos, target_vel)

    Notes:
    - dt is used to compute an exponential smoothing factor that behaves
      consistently across FPS.
    - No scene graph allocations inside update().
    """

    def __init__(self, camera_np, cfg: ChaseCameraConfig = ChaseCameraConfig()):
        self.camera_np = camera_np
        self.cfg = cfg

        # Cached current position for faster smoothing without getPos() calls.
        self._pos = None  # type: Optional[np.ndarray]

    def update(
        self,
        dt: float,
        target_pos: np.ndarray,
        target_vel: np.ndarray,
        *,
        up: np.ndarray = np.array([0.0, 0.0, 1.0], dtype=np.float32),
    ) -> None:
        p3d = require_panda3d()

        desired_pos, desired_look = compute_chase_camera_pose(
            target_pos, target_vel, up=up, cfg=self.cfg
        )

        if self._pos is None:
            # Initialize from current camera position.
            p = self.camera_np.getPos()
            self._pos = np.array([p.x, p.y, p.z], dtype=np.float32)

        # Exponential smoothing: alpha = 1 - exp(-dt/tau)
        tau = max(float(self.cfg.smoothing_tau), 1e-6)
        alpha = 1.0 - float(np.exp(-float(dt) / tau))

        self._pos = (1.0 - alpha) * self._pos + alpha * desired_pos

        self.camera_np.setPos(float(self._pos[0]), float(self._pos[1]), float(self._pos[2]))
        self.camera_np.lookAt(float(desired_look[0]), float(desired_look[1]), float(desired_look[2]))

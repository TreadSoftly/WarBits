from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import time

import numpy as np


@dataclass
class HUDState:
    last_t: float = 0.0
    fps_smooth: float = 0.0


def update_fps(hud: HUDState, *, now: Optional[float] = None, smooth: float = 0.9) -> float:
    """Exponential moving average FPS."""
    t = time.perf_counter() if now is None else float(now)
    if hud.last_t <= 0.0:
        hud.last_t = t
        hud.fps_smooth = 0.0
        return 0.0
    dt = max(1e-9, t - hud.last_t)
    fps = 1.0 / dt
    hud.fps_smooth = (smooth * hud.fps_smooth) + ((1.0 - smooth) * fps)
    hud.last_t = t
    return hud.fps_smooth


def draw_hud_text(ax, text: str, *, xy: Tuple[float, float] = (0.02, 0.98), color=(0.22, 1.0, 0.08, 1.0), fontsize: int = 10):
    """Draw overlay text in axes-normalized coordinates.

    Matplotlib 3D has no true HUD layer; `text2D` is the cleanest option.
    """
    # Keep a handle so caller can update/remove if desired.
    return ax.text2D(xy[0], xy[1], text, transform=ax.transAxes, color=color, fontsize=fontsize, va="top")


def format_basic_hud(*, fps: float, sim_t: float, player_alt_m: Optional[float] = None, player_speed_mps: Optional[float] = None) -> str:
    parts = [f"FPS {fps:6.1f}", f"t {sim_t:7.2f}s"]
    if player_alt_m is not None:
        parts.append(f"ALT {player_alt_m:7.0f} m")
    if player_speed_mps is not None:
        parts.append(f"SPD {player_speed_mps:6.1f} m/s")
    return "  ".join(parts)

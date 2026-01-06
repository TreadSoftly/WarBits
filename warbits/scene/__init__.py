# ── warbits/scene/__init__.py ───────────────────────────────────────────────
from __future__ import annotations

from importlib import import_module
from typing import Any

FRAME_RATE = 30  # ms between frames (≈33 fps)

__all__ = ["FRAME_RATE", "run_animation"]

def run_animation(*args: Any, **kwargs: Any) -> None:  # pragma: no cover
    """Convenience launcher for the full simulation window."""
    anim_mod = import_module("warbits.scene.animation")
    entry = getattr(anim_mod, "run_animation", None) or getattr(anim_mod, "main", None)
    if entry is None:
        raise RuntimeError("animation module has no run_animation()")
    entry(*args, **kwargs)

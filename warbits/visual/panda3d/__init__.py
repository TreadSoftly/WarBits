"""Panda3D wireframe rendering utilities (optional dependency).

This package MUST be safe to import even when Panda3D is not installed.
All Panda3D imports are guarded and only required when you actually construct
a Panda3D scene object.

v5 focuses on:
- A fast, batched line renderer for wireframe blueprints.
- Minimal helpers for coordinate mapping from sim-space to Panda3D-space.

"""

from __future__ import annotations

from .imports import Panda3DNotInstalled, is_panda3d_available, require_panda3d

__all__ = [
    "Panda3DNotInstalled",
    "is_panda3d_available",
    "require_panda3d",
]

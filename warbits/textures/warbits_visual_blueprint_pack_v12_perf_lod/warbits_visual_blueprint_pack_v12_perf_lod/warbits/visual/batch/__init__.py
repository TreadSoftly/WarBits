"""Batching helpers for high-FPS visuals.

The renderers (Matplotlib/Panda3D) should never create thousands of objects per frame.

This package provides preallocated batch builders that output:

- segments for `Line3DCollection` (Matplotlib)
- segment buffers for `GeomLines` batches (Panda3D)

Everything is built around *reuse*.
"""

from .projectiles import ProjectileSegmentBatch

__all__ = [
    "ProjectileSegmentBatch",
]

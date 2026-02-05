from __future__ import annotations

from typing import Any, TypeAlias

import numpy as np
from mpl_toolkits.mplot3d.art3d import Line3DCollection  # type: ignore[import-not-found]
from numpy.typing import NDArray

FloatArray: TypeAlias = NDArray[np.float64]


def terrain_wire_segments(x: FloatArray, y: FloatArray, z: FloatArray, *, stride: int = 4) -> FloatArray:
    """Build wireframe line segments for a heightfield grid.

    This avoids `ax.plot_wireframe`, which creates many Line3D objects and can be slow.

    Parameters:
        X, Y, Z: (H, W) arrays
        stride: sample step; larger == fewer lines == faster
    Returns:
        segments: (M, 2, 3) float array
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    z = np.asarray(z, dtype=float)

    if x.shape != y.shape or x.shape != z.shape or x.ndim != 2:
        raise ValueError("X, Y, Z must be same-shape 2D arrays")

    H, W = x.shape
    s = max(1, int(stride))

    # Count segments
    n_rows = len(range(0, H, s))
    n_cols = len(range(0, W, s))
    # rows: each row has (W-1) segments at stride 1 in columns (but we also stride columns)
    # We'll create segments along strided columns and strided rows for a coarse grid.
    row_cols = len(range(0, W, s))
    col_rows = len(range(0, H, s))

    total = 0
    # horizontal lines
    total += n_rows * max(0, row_cols - 1)
    # vertical lines
    total += n_cols * max(0, col_rows - 1)

    segs = np.empty((total, 2, 3), dtype=float)
    k = 0

    # Horizontal (vary col)
    cols = list(range(0, W, s))
    for r in range(0, H, s):
        for i in range(len(cols) - 1):
            c0 = cols[i]
            c1 = cols[i + 1]
            segs[k, 0, :] = (x[r, c0], y[r, c0], z[r, c0])
            segs[k, 1, :] = (x[r, c1], y[r, c1], z[r, c1])
            k += 1

    # Vertical (vary row)
    rows = list(range(0, H, s))
    for c in range(0, W, s):
        for i in range(len(rows) - 1):
            r0 = rows[i]
            r1 = rows[i + 1]
            segs[k, 0, :] = (x[r0, c], y[r0, c], z[r0, c])
            segs[k, 1, :] = (x[r1, c], y[r1, c], z[r1, c])
            k += 1

    return segs[:k]


def add_terrain_wire(
    ax: Any,
    x: FloatArray,
    y: FloatArray,
    z: FloatArray,
    *,
    color: tuple[float, float, float, float] = (0.11, 0.37, 0.13, 0.35),
    lw: float = 0.6,
    alpha: float = 0.35,
    stride: int = 4,
) -> Line3DCollection:
    segs = terrain_wire_segments(x, y, z, stride=stride)
    lc = Line3DCollection(segs, colors=[color], linewidths=lw, alpha=alpha)
    ax.add_collection3d(lc)
    return lc
    return lc

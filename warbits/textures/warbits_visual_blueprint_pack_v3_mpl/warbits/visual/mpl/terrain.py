from __future__ import annotations

from typing import Tuple

import numpy as np
from mpl_toolkits.mplot3d.art3d import Line3DCollection


def terrain_wire_segments(X: np.ndarray, Y: np.ndarray, Z: np.ndarray, *, stride: int = 4) -> np.ndarray:
    """Build wireframe line segments for a heightfield grid.

    This avoids `ax.plot_wireframe`, which creates many Line3D objects and can be slow.

    Parameters:
        X, Y, Z: (H, W) arrays
        stride: sample step; larger == fewer lines == faster
    Returns:
        segments: (M, 2, 3) float array
    """
    X = np.asarray(X, dtype=float)
    Y = np.asarray(Y, dtype=float)
    Z = np.asarray(Z, dtype=float)

    if X.shape != Y.shape or X.shape != Z.shape or X.ndim != 2:
        raise ValueError("X, Y, Z must be same-shape 2D arrays")

    H, W = X.shape
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
            segs[k, 0, :] = (X[r, c0], Y[r, c0], Z[r, c0])
            segs[k, 1, :] = (X[r, c1], Y[r, c1], Z[r, c1])
            k += 1

    # Vertical (vary row)
    rows = list(range(0, H, s))
    for c in range(0, W, s):
        for i in range(len(rows) - 1):
            r0 = rows[i]
            r1 = rows[i + 1]
            segs[k, 0, :] = (X[r0, c], Y[r0, c], Z[r0, c])
            segs[k, 1, :] = (X[r1, c], Y[r1, c], Z[r1, c])
            k += 1

    return segs[:k]


def add_terrain_wire(
    ax,
    X: np.ndarray,
    Y: np.ndarray,
    Z: np.ndarray,
    *,
    color=(0.11, 0.37, 0.13, 0.35),
    lw: float = 0.6,
    alpha: float = 0.35,
    stride: int = 4,
) -> Line3DCollection:
    segs = terrain_wire_segments(X, Y, Z, stride=stride)
    lc = Line3DCollection(segs, colors=[color], linewidths=lw, alpha=alpha)
    ax.add_collection3d(lc)
    return lc

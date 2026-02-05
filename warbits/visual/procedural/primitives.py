from __future__ import annotations

from typing import List, Sequence, Tuple

import numpy as np
from numpy.typing import NDArray

Edge = Tuple[int, int]


def _loop_edges(indices: Sequence[int]) -> List[Edge]:
    if len(indices) < 2:
        return []
    edges: List[Edge] = []
    for i in range(len(indices)):
        a = int(indices[i])
        b = int(indices[(i + 1) % len(indices)])
        if a != b:
            edges.append((a, b))
    return edges


# pyright: ignore[reportUnusedFunction]
def _strip_edges(indices: Sequence[int]) -> List[Edge]:
    if len(indices) < 2:
        return []
    edges: List[Edge] = []
    for i in range(len(indices) - 1):
        a = int(indices[i])
        b = int(indices[i + 1])
        if a != b:
            edges.append((a, b))
    return edges


def box(
    center_xyz: tuple[float, float, float],
    size_xyz: tuple[float, float, float],
) -> tuple[NDArray[np.float_], List[Edge]]:
    """Axis-aligned rectangular prism wireframe.

    Args:
        center_xyz: (x,y,z) center.
        size_xyz: (sx,sy,sz) full extents.

    Returns:
        vertices (8,3), edges (~12)
    """
    cx, cy, cz = center_xyz
    sx, sy, sz = size_xyz
    hx, hy, hz = 0.5 * sx, 0.5 * sy, 0.5 * sz

    # Vertex order: 0..3 bottom loop, 4..7 top loop (same winding)
    verts = np.array(
        [
            [cx - hx, cy - hy, cz - hz],
            [cx + hx, cy - hy, cz - hz],
            [cx + hx, cy + hy, cz - hz],
            [cx - hx, cy + hy, cz - hz],
            [cx - hx, cy - hy, cz + hz],
            [cx + hx, cy - hy, cz + hz],
            [cx + hx, cy + hy, cz + hz],
            [cx - hx, cy + hy, cz + hz],
        ],
        dtype=float,
    )

    edges: List[Edge] = []
    edges += _loop_edges([0, 1, 2, 3])
    edges += _loop_edges([4, 5, 6, 7])
    edges += [(0, 4), (1, 5), (2, 6), (3, 7)]
    return verts, edges


def cylinder(
    center_xyz: tuple[float, float, float],
    radius: float,
    length: float,
    *,
    axis: str = "x",
    segments: int = 12,
    caps: bool = True,
) -> tuple[NDArray[np.float_], List[Edge]]:
    """Cylinder wireframe with configurable axis.

    axis:
      - "x": cylinder length runs along +x/-x
      - "y": along +y/-y
      - "z": along +z/-z
    """
    axis = axis.lower().strip()
    assert axis in ("x", "y", "z"), "axis must be x/y/z"

    cx, cy, cz = center_xyz
    half = 0.5 * float(length)
    seg = int(max(3, segments))

    theta = np.linspace(0.0, 2.0 * np.pi, seg, endpoint=False)
    c = np.cos(theta)
    s = np.sin(theta)

    # Two rings
    ring0 = np.stack([c, s], axis=1) * float(radius)
    ring1 = ring0.copy()

    if axis == "x":
        ring0_verts = np.column_stack([np.full(seg, cx - half), cy + ring0[:, 0], cz + ring0[:, 1]])
        ring1_verts = np.column_stack([np.full(seg, cx + half), cy + ring1[:, 0], cz + ring1[:, 1]])
    elif axis == "y":
        ring0_verts = np.column_stack([cx + ring0[:, 0], np.full(seg, cy - half), cz + ring0[:, 1]])
        ring1_verts = np.column_stack([cx + ring1[:, 0], np.full(seg, cy + half), cz + ring1[:, 1]])
    else:
        ring0_verts = np.column_stack([cx + ring0[:, 0], cy + ring0[:, 1], np.full(seg, cz - half)])
        ring1_verts = np.column_stack([cx + ring1[:, 0], cy + ring1[:, 1], np.full(seg, cz + half)])

    verts = np.vstack([ring0_verts, ring1_verts]).astype(float)

    edges: List[Edge] = []
    edges += _loop_edges(list(range(0, seg)))
    edges += _loop_edges(list(range(seg, 2 * seg)))
    edges += [(i, seg + i) for i in range(seg)]  # longitudinal ribs

    if caps:
        # Add simple cross on each cap to make it read better at distance
        edges += [
            (0, seg // 2),
            (seg // 4, (3 * seg) // 4),
            (seg, seg + seg // 2),
            (seg + seg // 4, seg + (3 * seg) // 4),
        ]

    return verts, edges


def cone(
    base_center_xyz: tuple[float, float, float],
    radius: float,
    length: float,
    *,
    axis: str = "x",
    segments: int = 12,
) -> tuple[NDArray[np.float_], List[Edge]]:
    """Cone wireframe (useful for noses)."""
    axis = axis.lower().strip()
    assert axis in ("x", "y", "z"), "axis must be x/y/z"
    bx, by, bz = base_center_xyz
    seg = int(max(3, segments))

    theta = np.linspace(0.0, 2.0 * np.pi, seg, endpoint=False)
    c = np.cos(theta)
    s = np.sin(theta)

    ring = np.stack([c, s], axis=1) * float(radius)

    if axis == "x":
        base = np.column_stack([np.full(seg, bx), by + ring[:, 0], bz + ring[:, 1]])
        tip = np.array([[bx + float(length), by, bz]], dtype=float)
    elif axis == "y":
        base = np.column_stack([bx + ring[:, 0], np.full(seg, by), bz + ring[:, 1]])
        tip = np.array([[bx, by + float(length), bz]], dtype=float)
    else:
        base = np.column_stack([bx + ring[:, 0], by + ring[:, 1], np.full(seg, bz)])
        tip = np.array([[bx, by, bz + float(length)]], dtype=float)

    verts = np.vstack([base, tip]).astype(float)
    tip_idx = seg

    edges: List[Edge] = []
    edges += _loop_edges(list(range(seg)))
    for i in range(seg):
        edges.append((i, tip_idx))
    return verts, edges


def merge(parts: Sequence[tuple[NDArray[np.float_], List[Edge]]]) -> tuple[NDArray[np.float_], List[Edge]]:
    """Merge multiple primitives into one vertex/edge set."""
    vertices: List[NDArray[np.float_]] = []
    edges: List[Edge] = []
    offset = 0
    for verts, seg_edges in parts:
        verts = np.asarray(verts, dtype=float)
        vertices.append(verts)
        for a, b in seg_edges:
            edges.append((int(a) + offset, int(b) + offset))
        offset += int(verts.shape[0])
    if not vertices:
        return np.zeros((0, 3), dtype=float), []
    return np.vstack(vertices), edges


if False:  # pragma: no cover
    _strip_edges([])

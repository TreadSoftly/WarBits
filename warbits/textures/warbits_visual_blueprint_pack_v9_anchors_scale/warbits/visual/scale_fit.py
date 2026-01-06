from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Mapping, Dict, Any, Tuple, List

import numpy as np


@dataclass(frozen=True)
class TargetDims:
    """
    Physical dimensions (meters).

    Any field can be None if unknown.
    """
    length_m: Optional[float] = None   # x extent
    span_m: Optional[float] = None     # y extent (wingspan / track width)
    height_m: Optional[float] = None   # z extent

    def as_dict(self) -> Dict[str, float]:
        out: Dict[str, float] = {}
        if self.length_m is not None:
            out["length_m"] = float(self.length_m)
        if self.span_m is not None:
            out["span_m"] = float(self.span_m)
        if self.height_m is not None:
            out["height_m"] = float(self.height_m)
        return out


def bounds_from_vertices(vertices_m: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    V = np.asarray(vertices_m, dtype=float)
    if V.ndim != 2 or V.shape[1] != 3 or V.shape[0] < 2:
        raise ValueError("vertices_m must be (N,3) with N>=2")
    return V.min(axis=0), V.max(axis=0)


def dims_from_vertices(vertices_m: np.ndarray) -> np.ndarray:
    vmin, vmax = bounds_from_vertices(vertices_m)
    return vmax - vmin


def compute_uniform_scale(vertices_m: np.ndarray, target: TargetDims) -> float:
    """
    Compute a single scalar scale factor that best matches any provided target dims.

    Strategy:
      - compute ratios per available axis
      - take the median (robust to one bad axis)
    """
    dims = dims_from_vertices(vertices_m)

    ratios: List[float] = []
    eps = 1e-9

    if target.length_m is not None and dims[0] > eps:
        ratios.append(float(target.length_m) / float(dims[0]))
    if target.span_m is not None and dims[1] > eps:
        ratios.append(float(target.span_m) / float(dims[1]))
    if target.height_m is not None and dims[2] > eps:
        ratios.append(float(target.height_m) / float(dims[2]))

    if not ratios:
        return 1.0

    ratios_sorted = sorted(ratios)
    mid = len(ratios_sorted) // 2
    if len(ratios_sorted) % 2 == 1:
        return ratios_sorted[mid]
    return 0.5 * (ratios_sorted[mid - 1] + ratios_sorted[mid])


def compute_nonuniform_scale(vertices_m: np.ndarray, target: TargetDims) -> np.ndarray:
    """
    Compute per-axis scale factors [sx, sy, sz].

    - Unspecified axes default to 1.0.
    - Useful for stretching a procedural placeholder blueprint to match known dims.

    NOTE: Use with care: it distorts the shape.
    """
    dims = dims_from_vertices(vertices_m)
    eps = 1e-9

    s = np.ones(3, dtype=float)

    if target.length_m is not None and dims[0] > eps:
        s[0] = float(target.length_m) / float(dims[0])
    if target.span_m is not None and dims[1] > eps:
        s[1] = float(target.span_m) / float(dims[1])
    if target.height_m is not None and dims[2] > eps:
        s[2] = float(target.height_m) / float(dims[2])

    return s


def apply_scale(vertices_m: np.ndarray, scale: float | np.ndarray) -> np.ndarray:
    V = np.asarray(vertices_m, dtype=float)
    if isinstance(scale, np.ndarray):
        s = np.asarray(scale, dtype=float).reshape(3,)
        return V * s
    return V * float(scale)

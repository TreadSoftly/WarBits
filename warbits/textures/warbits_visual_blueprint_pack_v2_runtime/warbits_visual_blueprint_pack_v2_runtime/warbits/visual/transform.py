from __future__ import annotations

from typing import Iterable, Optional, Tuple

import numpy as np

from .blueprint_schema import Edge, Vec3


def transform_vertices(
    vertices_m: np.ndarray,
    rotation_m: Optional[np.ndarray] = None,
    translation_m: Optional[np.ndarray] = None,
) -> np.ndarray:
    """Transform vertices by rotation + translation.

    Parameters
    ----------
    vertices_m:
        Array of shape (N,3), float.
    rotation_m:
        Optional rotation matrix of shape (3,3). If None, identity.
    translation_m:
        Optional translation vector of shape (3,). If None, zeros.

    Returns
    -------
    np.ndarray
        Transformed vertices (N,3) float64.

    Notes
    -----
    - This is a hot-path helper; keep it allocation-light.
    - Callers can cast to float32 if needed.
    """
    v = vertices_m
    if rotation_m is not None:
        v = v @ rotation_m.T
    if translation_m is not None:
        v = v + translation_m
    return v


def build_segments(
    vertices_m: np.ndarray,
    edges: np.ndarray,
    rotation_m: Optional[np.ndarray] = None,
    translation_m: Optional[np.ndarray] = None,
) -> np.ndarray:
    """Build transformed line segments.

    Parameters
    ----------
    vertices_m:
        (N,3)
    edges:
        (M,2) int
    rotation_m:
        (3,3) or None
    translation_m:
        (3,) or None

    Returns
    -------
    segments: (M,2,3)
    """
    # Local segments: (M,2,3)
    seg = vertices_m[edges]
    if rotation_m is None and translation_m is None:
        return seg

    # Transform with minimal allocations: flatten to (M*2,3)
    flat = seg.reshape(-1, 3)
    flat_t = transform_vertices(flat, rotation_m=rotation_m, translation_m=translation_m)
    return flat_t.reshape(seg.shape)

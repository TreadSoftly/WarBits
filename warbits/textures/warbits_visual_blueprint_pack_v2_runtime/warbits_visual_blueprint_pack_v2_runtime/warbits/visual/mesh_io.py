from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator, Tuple, TypeAlias

import numpy as np
from numpy.typing import NDArray

try:
    import trimesh  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    trimesh = None  # type: ignore[assignment]

TrimeshLike: TypeAlias = Any
SceneLike: TypeAlias = Any

FloatArray: TypeAlias = NDArray[np.float64]


def require_trimesh() -> Any:
    if trimesh is None:
        raise ImportError("trimesh is required for visual blueprint ingestion. " "Install with: pip install trimesh")
    return trimesh


def load_any_mesh(path: str | Path, force_scene: bool = True) -> TrimeshLike | SceneLike:
    """Load a mesh file via trimesh.

    For multi-mesh files, prefer returning a Scene (force_scene=True).
    """
    tm = require_trimesh()
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)

    obj = tm.load(str(p), force="scene" if force_scene else None)
    return obj


def iter_scene_meshes(scene: SceneLike) -> Iterator[Tuple[str, TrimeshLike]]:
    """Yield (name, mesh) for each geometry in a trimesh.Scene."""
    for name, geom in scene.geometry.items():
        if hasattr(geom, "faces") and hasattr(geom, "vertices"):
            yield name, geom


def scene_to_merged_mesh(scene: SceneLike) -> TrimeshLike:
    """Merge all geometry in a Scene into a single Trimesh."""
    tm = require_trimesh()
    meshes = [g for _, g in iter_scene_meshes(scene)]
    if not meshes:
        raise ValueError("Scene contains no mesh geometry")
    merged = tm.util.concatenate(meshes)
    return merged


def center_vertices(vertices: FloatArray) -> FloatArray:
    """Center vertices around origin by subtracting centroid."""
    c = vertices.mean(axis=0)
    return vertices - c

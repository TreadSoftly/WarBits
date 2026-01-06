from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Tuple, Union

import numpy as np

try:
    import trimesh
except Exception:  # pragma: no cover
    trimesh = None  # type: ignore


TrimeshLike = "trimesh.Trimesh"
SceneLike = "trimesh.Scene"


def require_trimesh() -> "trimesh":
    if trimesh is None:
        raise ImportError(
            "trimesh is required for visual blueprint ingestion. "
            "Install with: pip install trimesh"
        )
    return trimesh


def load_any_mesh(path: str | Path, force_scene: bool = True) -> Union["trimesh.Trimesh", "trimesh.Scene"]:
    """Load a mesh file via trimesh.

    For multi-mesh files, prefer returning a Scene (force_scene=True).
    """
    tm = require_trimesh()
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)

    obj = tm.load(str(p), force="scene" if force_scene else None)
    return obj


def iter_scene_meshes(scene: "trimesh.Scene") -> Iterator[Tuple[str, "trimesh.Trimesh"]]:
    """Yield (name, mesh) for each geometry in a trimesh.Scene."""
    for name, geom in scene.geometry.items():
        if hasattr(geom, "faces") and hasattr(geom, "vertices"):
            yield name, geom


def scene_to_merged_mesh(scene: "trimesh.Scene") -> "trimesh.Trimesh":
    """Merge all geometry in a Scene into a single Trimesh."""
    tm = require_trimesh()
    meshes = [g for _, g in iter_scene_meshes(scene)]
    if not meshes:
        raise ValueError("Scene contains no mesh geometry")
    merged = tm.util.concatenate(meshes)
    return merged


def center_vertices(vertices: np.ndarray) -> np.ndarray:
    """Center vertices around origin by subtracting centroid."""
    c = vertices.mean(axis=0)
    return vertices - c

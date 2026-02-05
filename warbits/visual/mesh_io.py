from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Iterator, Mapping, Optional, Protocol, Tuple, cast

import numpy as np
from numpy.typing import NDArray

try:
    _trimesh = importlib.import_module("trimesh")
except Exception:  # pragma: no cover
    _trimesh = None


class TrimeshLike(Protocol):
    faces: NDArray[np.int_]
    vertices: NDArray[np.float_]


@dataclass(frozen=True)
class MeshData:
    name: str
    vertices: NDArray[np.float_]  # (N,3) float64
    faces: NDArray[np.int_]  # (M,3) int64, triangles


class SceneLike(Protocol):
    geometry: Mapping[str, TrimeshLike]


def require_trimesh() -> ModuleType:
    if _trimesh is None:
        raise ImportError(
            "trimesh is required for visual blueprint ingestion. "
            "Install with: pip install trimesh"
        )
    return _trimesh


def load_any_mesh(path: str | Path, force_scene: bool = True) -> TrimeshLike | SceneLike:
    """Load a mesh file via trimesh.

    For multi-mesh files, prefer returning a Scene (force_scene=True).
    """
    tm = require_trimesh()
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)

    obj = tm.load(str(p), force="scene" if force_scene else None)
    return cast(TrimeshLike | SceneLike, obj)


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
    return cast(TrimeshLike, merged)


def center_vertices(vertices: NDArray[np.float_]) -> NDArray[np.float_]:
    """Center vertices around origin by subtracting centroid."""
    c = vertices.mean(axis=0)
    return vertices - c


def read_obj_mesh(path: str | Path) -> MeshData:
    """Read an OBJ into a single mesh.

    If the OBJ contains multiple objects, this returns a mesh named "__combined__".
    Use `read_obj_objects` if you need per-object splitting.
    """
    objs = read_obj_objects(path)
    if not objs:
        raise ValueError(f"No geometry in OBJ: {path}")
    if len(objs) == 1:
        return next(iter(objs.values()))
    verts: list[NDArray[np.float_]] = []
    faces: list[NDArray[np.int_]] = []
    v_base = 0
    for m in objs.values():
        verts.append(m.vertices)
        faces.append(m.faces + v_base)
        v_base += len(m.vertices)
    vertices_all = np.vstack(verts)
    faces_all = np.vstack(faces)
    return MeshData(name="__combined__", vertices=vertices_all, faces=faces_all)


def read_obj_objects(path: str | Path) -> dict[str, MeshData]:
    """Read an OBJ and split meshes by `o <name>` (or `g <name>` if no `o`).

    - Triangulates polygons.
    - Ignores materials.
    - Handles negative indices.
    - Compacts each mesh to only used vertices.
    """
    p = Path(path)
    vertices: list[list[float]] = []
    objects_faces: dict[str, list[list[int]]] = {}
    current: Optional[str] = None

    def ensure_current() -> str:
        nonlocal current
        if current is None:
            current = "__default__"
        objects_faces.setdefault(current, [])
        return current

    with p.open("r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("o "):
                current = line[2:].strip() or "__unnamed__"
                objects_faces.setdefault(current, [])
                continue
            if line.startswith("g ") and current is None:
                current = line[2:].strip() or "__unnamed__"
                objects_faces.setdefault(current, [])
                continue
            if line.startswith("v "):
                parts = line.split()
                if len(parts) >= 4:
                    vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
                continue
            if line.startswith("f "):
                curr = ensure_current()
                toks = line.split()[1:]
                idx: list[int] = []
                for t in toks:
                    v = int(t.split("/")[0])
                    if v < 0:
                        v = len(vertices) + 1 + v
                    idx.append(v - 1)
                if len(idx) < 3:
                    continue
                for i in range(1, len(idx) - 1):
                    objects_faces[curr].append([idx[0], idx[i], idx[i + 1]])
                continue

    if not vertices:
        return {}

    v_all = np.asarray(vertices, dtype=np.float64)

    out: dict[str, MeshData] = {}
    for name, faces_list in objects_faces.items():
        if not faces_list:
            continue
        f_all = np.asarray(faces_list, dtype=np.int64)
        used = np.unique(f_all.reshape(-1))
        mapping = {int(old): i for i, old in enumerate(used.tolist())}
        v_mesh = v_all[used]
        f_mesh = np.vectorize(mapping.get)(f_all)
        out[name] = MeshData(name=name, vertices=v_mesh, faces=f_mesh)
    return out

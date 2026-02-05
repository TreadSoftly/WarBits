from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, cast

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class MeshData:
    name: str
    vertices: NDArray[np.float_]  # (N,3) float64
    faces: NDArray[np.int_]  # (M,3) int64, triangles


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
    # combine
    verts: list[NDArray[np.float_]] = []
    faces: list[NDArray[np.int_]] = []
    v_base = 0
    for m in objs.values():
        verts.append(m.vertices)
        faces.append(m.faces + v_base)
        v_base += len(m.vertices)
    V = np.vstack(verts)
    F = np.vstack(faces)
    return MeshData(name="__combined__", vertices=V, faces=F)


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
                # Use group name only if there is no object name so far.
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
                # triangulate fan
                if len(idx) < 3:
                    continue
                for i in range(1, len(idx) - 1):
                    objects_faces[curr].append([idx[0], idx[i], idx[i + 1]])
                continue

    if not vertices:
        return {}

    V_all = np.asarray(vertices, dtype=np.float64)

    out: dict[str, MeshData] = {}
    for name, faces_list in objects_faces.items():
        if not faces_list:
            continue
        F_all = np.asarray(faces_list, dtype=np.int64)
        used = np.unique(F_all.reshape(-1))
        mapping = {int(old): i for i, old in enumerate(used.tolist())}
        V = V_all[used]
        # remap faces
        F = np.vectorize(mapping.get)(F_all)
        out[name] = MeshData(name=name, vertices=V, faces=F)
    return out


def load_gltf_scene_optional(path: str | Path) -> dict[str, MeshData]:
    """Load GLB/GLTF using trimesh if available.

    This is optional so the main pipeline can stay lightweight.
    If trimesh isn't installed, raise a clear error.
    """
    try:
        import trimesh  # type: ignore
    except Exception as e:
        raise ImportError("GLTF/GLB loading requires 'trimesh'. Install it or export assets to OBJ.") from e

    scene = cast(Any, trimesh).load(str(path), force="scene")
    out: dict[str, MeshData] = {}
    if hasattr(scene, "geometry"):
        for i, (name, geom) in enumerate(cast(dict[str, Any], scene.geometry).items()):
            mesh = geom
            vertices_arr = np.asarray(mesh.vertices, dtype=np.float64)
            faces_arr = np.asarray(mesh.faces, dtype=np.int64)
            nm = str(name) if name else f"mesh_{i:03d}"
            out[nm] = MeshData(name=nm, vertices=vertices_arr, faces=faces_arr)
    else:
        # a single mesh
        mesh = scene
        vertices_arr = np.asarray(mesh.vertices, dtype=np.float64)
        faces_arr = np.asarray(mesh.faces, dtype=np.int64)
        out["__mesh__"] = MeshData(name="__mesh__", vertices=vertices_arr, faces=faces_arr)
    return out

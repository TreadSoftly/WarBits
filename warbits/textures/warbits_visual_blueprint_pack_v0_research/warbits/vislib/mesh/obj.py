from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ObjMesh:
    vertices: list[tuple[float, float, float]]
    faces: list[tuple[int, ...]]  # 0-based vertex indices


def _parse_face_vertex(token: str) -> int:
    # token can be: "v", "v/vt", "v//vn", "v/vt/vn"
    # we only need vertex index
    parts = token.split("/")
    if not parts[0]:
        raise ValueError(f"Invalid face token: {token!r}")
    idx = int(parts[0])
    # OBJ indices are 1-based; negative indices are relative to end
    return idx


def load_obj(path: str, *, triangulate: bool = True) -> ObjMesh:
    """Minimal OBJ loader (positions + faces).

    Supports:
    - v lines
    - f lines with vertex indices (vt/vn ignored)

    This is intentionally tiny: no materials, no normals, no UVs.
    """
    verts: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("v "):
                _, xs, ys, zs, *_rest = line.split()
                verts.append((float(xs), float(ys), float(zs)))
            elif line.startswith("f "):
                parts = line.split()[1:]
                idxs: list[int] = []
                for p in parts:
                    raw = _parse_face_vertex(p)
                    if raw < 0:
                        raw = len(verts) + 1 + raw  # raw is negative
                    idxs.append(raw - 1)
                if len(idxs) < 3:
                    continue
                if triangulate and len(idxs) > 3:
                    # fan triangulate (0, i, i+1)
                    a = idxs[0]
                    for i in range(1, len(idxs) - 1):
                        faces.append((a, idxs[i], idxs[i + 1]))
                else:
                    faces.append(tuple(idxs))
    if not verts:
        raise ValueError(f"No vertices found in OBJ: {path}")
    return ObjMesh(vertices=verts, faces=faces)
    return ObjMesh(vertices=verts, faces=faces)
    return ObjMesh(vertices=verts, faces=faces)

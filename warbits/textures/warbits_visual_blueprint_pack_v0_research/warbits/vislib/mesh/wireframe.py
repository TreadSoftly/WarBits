from __future__ import annotations

import math
from collections import defaultdict
from typing import Iterable

Vec3 = tuple[float, float, float]
Edge = tuple[int, int]
Face = tuple[int, int, int]  # triangles only here


def edges_from_faces(faces: Iterable[tuple[int, ...]]) -> list[Edge]:
    """Return unique undirected edges from faces."""
    es: set[Edge] = set()
    for f in faces:
        if len(f) < 3:
            continue
        for i in range(len(f)):
            a = int(f[i])
            b = int(f[(i + 1) % len(f)])
            if a == b:
                continue
            if a > b:
                a, b = b, a
            es.add((a, b))
    return sorted(es)


def _sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _norm(a: Vec3) -> float:
    return math.sqrt(_dot(a, a))


def _unit(a: Vec3) -> Vec3:
    n = _norm(a)
    if n <= 1e-12:
        return (0.0, 0.0, 0.0)
    return (a[0] / n, a[1] / n, a[2] / n)


def face_normal(vertices: list[Vec3], tri: Face) -> Vec3:
    a, b, c = tri
    ab = _sub(vertices[b], vertices[a])
    ac = _sub(vertices[c], vertices[a])
    n = _cross(ab, ac)
    return _unit(n)


def feature_edges(
    vertices: list[Vec3],
    faces_tris: list[Face],
    *,
    crease_angle_deg: float = 35.0,
    include_boundaries: bool = True,
) -> list[Edge]:
    """Extract 'feature edges' from a triangle mesh.

    An edge is included if:
    - it's a boundary (only 1 adjacent face) and include_boundaries=True
    - or the dihedral angle between its two adjacent face normals >= crease_angle_deg

    This helps produce a clean wireframe that doesn't draw every interior triangulation edge.
    """
    if crease_angle_deg < 0:
        raise ValueError("crease_angle_deg must be >= 0")
    cos_thresh = math.cos(math.radians(crease_angle_deg))

    # map edge -> adjacent face normals
    adj: dict[Edge, list[Vec3]] = defaultdict(list)

    for tri in faces_tris:
        n = face_normal(vertices, tri)
        a, b, c = tri
        edges = [(a, b), (b, c), (c, a)]
        for u, v in edges:
            if u > v:
                u, v = v, u
            adj[(u, v)].append(n)

    out: list[Edge] = []
    for e, normals in adj.items():
        if len(normals) == 1:
            if include_boundaries:
                out.append(e)
            continue
        if len(normals) >= 2:
            # take first two faces (manifold assumption)
            n1, n2 = normals[0], normals[1]
            d = _dot(n1, n2)
            # if normals are near-zero, treat as feature
            if abs(d) < 1e-8:
                out.append(e)
                continue
            # if d <= cos_thresh, angle >= threshold
            if d <= cos_thresh:
                out.append(e)
    return sorted(out)

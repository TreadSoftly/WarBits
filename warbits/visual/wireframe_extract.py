from __future__ import annotations

import importlib
from dataclasses import dataclass
from types import ModuleType
from typing import Dict, Protocol, Tuple

import numpy as np
from numpy.typing import NDArray

from .mesh_io import MeshData

try:
    _trimesh = importlib.import_module("trimesh")
except Exception:  # pragma: no cover
    _trimesh = None


class TrimeshLike(Protocol):
    faces: NDArray[np.int_] | None
    vertices: NDArray[np.float64]
    face_adjacency_edges: NDArray[np.int_]
    face_adjacency_angles: NDArray[np.float_]
    face_adjacency: NDArray[np.int_]
    edges_unique: NDArray[np.int_]
    edges_unique_inverse: NDArray[np.int_]


def require_trimesh() -> ModuleType:
    if _trimesh is None:
        raise ImportError(
            "trimesh is required for visual blueprint ingestion. "
            "Install with: pip install trimesh"
        )
    return _trimesh


@dataclass(frozen=True)
class LODSpec:
    name: str
    feature_angle_deg: float
    max_edges: int
    sample_rate: float = 1.0
    include_boundary: bool = True
    include_ribs: bool = False
    ribs_slices: int = 0


@dataclass(frozen=True)
class WireframeExtractParams:
    """Parameters for extracting a view-independent wireframe from a triangle mesh."""

    crease_angle_deg: float = 35.0
    max_edges: int = 5000
    min_edges: int = 400
    extra_rib_fraction: float = 0.03  # add a few extra edges for detail
    seed: int = 1337


def extract_wireframe_edges(
    mesh: TrimeshLike | MeshData,
    feature_angle_deg: float = 30.0,
    max_edges: int = 8000,
    sample_rate: float = 1.0,
    include_boundary: bool = True,
    rng_seed: int = 1234,
    params: WireframeExtractParams | None = None,
) -> NDArray[np.int_] | list[tuple[int, int]]:
    """Extract an edge list suitable for a 'wireframe' outline look.

    Strategy:
    - crease edges (dihedral angle > feature threshold)
    - boundary edges (edges used by only 1 face), if requested
    - deterministic downsample to max_edges

    Returns
    -------
    edges: (M,2) int32
    """
    if params is not None:
        if isinstance(mesh, MeshData):
            return _extract_wireframe_edges_meshdata(mesh, params)
        raise TypeError("params is only supported for MeshData inputs")

    if isinstance(mesh, MeshData):
        raise TypeError("MeshData inputs require params")

    require_trimesh()  # ensures trimesh import
    if not hasattr(mesh, "faces") or mesh.faces is None:
        raise ValueError("mesh must have faces")

    # Ensure adjacency is computed
    # face_adjacency_edges: (K,2) edges between adjacent faces
    # face_adjacency_angles: (K,) dihedral angles in radians
    try:
        adj_edges = mesh.face_adjacency_edges
        adj_angles = mesh.face_adjacency_angles
    except Exception:
        # Force compute
        _ = mesh.face_adjacency
        adj_edges = mesh.face_adjacency_edges
        adj_angles = mesh.face_adjacency_angles

    # Feature edges by dihedral angle
    angle_rad = np.deg2rad(float(feature_angle_deg))
    feat_mask = adj_angles > angle_rad
    feat_edges = adj_edges[feat_mask] if len(adj_edges) else np.zeros((0, 2), dtype=np.int64)

    edges = feat_edges

    if include_boundary:
        # boundary edges are those which appear only once in mesh edges
        # Use mesh.edges_unique and mesh.edges_unique_inverse to count
        unique = mesh.edges_unique
        inv = mesh.edges_unique_inverse
        # Count occurrences
        counts = np.bincount(inv, minlength=len(unique))
        boundary = unique[counts == 1] if len(unique) else np.zeros((0, 2), dtype=np.int64)
        edges = np.vstack([edges, boundary]) if len(edges) or len(boundary) else np.zeros((0, 2), dtype=np.int64)

    if len(edges) == 0:
        return np.zeros((0, 2), dtype=np.int32)

    # Normalize edge ordering (a<b) and dedupe
    a = np.minimum(edges[:, 0], edges[:, 1])
    b = np.maximum(edges[:, 0], edges[:, 1])
    edges = np.stack([a, b], axis=1)
    edges = np.unique(edges, axis=0)

    # Deterministic sample
    if sample_rate < 1.0 and len(edges) > 0:
        rng = np.random.default_rng(int(rng_seed))
        keep = rng.random(len(edges)) < float(sample_rate)
        edges = edges[keep]

    if max_edges and len(edges) > int(max_edges):
        rng = np.random.default_rng(int(rng_seed))
        idx = rng.choice(len(edges), size=int(max_edges), replace=False)
        edges = edges[idx]

    return edges.astype(np.int32)


def _extract_wireframe_edges_meshdata(
    mesh: MeshData,
    params: WireframeExtractParams,
) -> list[tuple[int, int]]:
    """Extract wireframe edges for MeshData using a deterministic heuristic."""
    v = mesh.vertices
    f = mesh.faces
    if len(v) == 0 or len(f) == 0:
        return []

    crease = np.deg2rad(float(params.crease_angle_deg))
    normals = _face_normals(v, f)

    edge_faces: dict[tuple[int, int], list[int]] = {}
    for fi, tri in enumerate(f):
        a, b, c = int(tri[0]), int(tri[1]), int(tri[2])
        edges = [(a, b), (b, c), (c, a)]
        for u, w in edges:
            if u > w:
                u, w = w, u
            edge_faces.setdefault((u, w), []).append(fi)

    boundary: list[tuple[int, int]] = []
    feature: list[tuple[int, int]] = []
    all_edges: list[tuple[int, int]] = sorted(edge_faces.keys())

    for e in all_edges:
        faces = edge_faces[e]
        if len(faces) == 1:
            boundary.append(e)
        elif len(faces) == 2:
            n1 = normals[faces[0]]
            n2 = normals[faces[1]]
            dot = float(np.clip(np.dot(n1, n2), -1.0, 1.0))
            ang = float(np.arccos(dot))
            if ang >= crease:
                feature.append(e)
        else:
            feature.append(e)

    cand_set = set(boundary)
    cand_set.update(feature)
    candidates: list[tuple[int, int]] = list(cand_set)

    rng = np.random.default_rng(int(params.seed))
    if params.extra_rib_fraction > 0.0:
        others: list[tuple[int, int]] = [e for e in all_edges if e not in cand_set]
        if others:
            k = int(max(0, round(len(all_edges) * float(params.extra_rib_fraction))))
            if k > 0:
                idx = np.arange(len(others))
                rng.shuffle(idx)
                add: list[tuple[int, int]] = [others[i] for i in idx[:k]]
                candidates.extend(add)

    max_edges = int(params.max_edges)
    min_edges = int(params.min_edges)

    if len(candidates) == 0:
        candidates = all_edges

    def edge_len(e: tuple[int, int]) -> float:
        a, b = e
        return float(np.linalg.norm(v[b] - v[a]))

    lens = np.array([edge_len(e) for e in candidates], dtype=np.float64)
    order = np.argsort(-lens)
    if len(candidates) > max_edges:
        keep_idx = order[:max_edges]
        candidates = [candidates[int(i)] for i in keep_idx]
    elif len(candidates) < min_edges and len(all_edges) > len(candidates):
        extra: list[tuple[int, int]] = [e for e in all_edges if e not in set(candidates)]
        extra_lens = np.array([edge_len(e) for e in extra], dtype=np.float64)
        extra_order = np.argsort(-extra_lens)
        need = min_edges - len(candidates)
        add: list[tuple[int, int]] = [extra[int(i)] for i in extra_order[:need]]
        candidates.extend(add)

    return sorted(set(candidates))


def _face_normals(vertices: NDArray[np.float_], faces: NDArray[np.int_]) -> NDArray[np.float_]:
    v0 = vertices[faces[:, 0]]
    v1 = vertices[faces[:, 1]]
    v2 = vertices[faces[:, 2]]
    n = np.cross(v1 - v0, v2 - v0)
    lens = np.linalg.norm(n, axis=1)
    lens = np.where(lens < 1e-12, 1.0, lens)
    return n / lens[:, None]


def generate_rib_edges(
    mesh: TrimeshLike,
    axis: int = 0,
    slices: int = 8,
    thickness_frac: float = 0.03,
    rng_seed: int = 1234,
    max_edges: int = 1500,
) -> NDArray[np.int_]:
    """Generate synthetic 'rib' edges to create internal structure hints.

    This is a stylistic tool: it does not try to be an engineering-accurate frame.

    Method:
    - take slices along the chosen axis (default X)
    - find extreme vertices in other axes within each slice
    - connect those extremes into a simple diamond loop

    Returns
    -------
    edges: (M,2) int32, referencing existing mesh vertices
    """
    v = np.asarray(mesh.vertices, dtype=np.float64)
    if v.shape[0] < 8 or slices <= 0:
        return np.zeros((0, 2), dtype=np.int32)

    ax = int(axis) % 3
    other = [i for i in range(3) if i != ax]
    mn = float(v[:, ax].min())
    mx = float(v[:, ax].max())
    span = mx - mn
    if span <= 1e-9:
        return np.zeros((0, 2), dtype=np.int32)

    thick = float(thickness_frac) * span
    # slice positions avoid the extreme ends
    positions = np.linspace(mn + span * 0.1, mx - span * 0.1, int(slices))

    edges_out: list[tuple[int, int]] = []
    rng = np.random.default_rng(int(rng_seed))

    for s in positions:
        mask = np.abs(v[:, ax] - s) <= thick
        idx = np.nonzero(mask)[0]
        if len(idx) < 12:
            continue

        pts = v[idx]

        # Extreme indices along the other axes
        ymin_i = idx[int(np.argmin(pts[:, other[0]]))]
        ymax_i = idx[int(np.argmax(pts[:, other[0]]))]
        zmin_i = idx[int(np.argmin(pts[:, other[1]]))]
        zmax_i = idx[int(np.argmax(pts[:, other[1]]))]

        ring = [ymin_i, zmax_i, ymax_i, zmin_i]
        for a, b in zip(ring, ring[1:] + ring[:1]):
            if a != b:
                edges_out.append((int(a), int(b)))

    if not edges_out:
        return np.zeros((0, 2), dtype=np.int32)

    edges = np.asarray(edges_out, dtype=np.int32)

    # Dedupe
    a = np.minimum(edges[:, 0], edges[:, 1])
    b = np.maximum(edges[:, 0], edges[:, 1])
    edges = np.stack([a, b], axis=1)
    edges = np.unique(edges, axis=0)

    if max_edges and len(edges) > int(max_edges):
        idx = rng.choice(len(edges), size=int(max_edges), replace=False)
        edges = edges[idx]

    return edges.astype(np.int32)


def extract_lod_edge_sets(
    mesh: TrimeshLike,
    lods: Tuple[LODSpec, ...],
    rng_seed: int = 1234,
) -> Dict[str, NDArray[np.int_]]:
    """Extract multiple LOD edge sets from a mesh."""
    out: Dict[str, NDArray[np.int_]] = {}
    for i, spec in enumerate(lods):
        edges = extract_wireframe_edges(
            mesh,
            feature_angle_deg=spec.feature_angle_deg,
            max_edges=spec.max_edges,
            sample_rate=spec.sample_rate,
            include_boundary=spec.include_boundary,
            rng_seed=rng_seed + i * 17,
        )
        if spec.include_ribs and spec.ribs_slices > 0:
            ribs = generate_rib_edges(
                mesh,
                axis=0,
                slices=spec.ribs_slices,
                thickness_frac=0.03,
                rng_seed=rng_seed + i * 17 + 9,
                max_edges=max(200, int(spec.max_edges * 0.25)),
            )
            if len(ribs):
                edges = np.vstack([edges, ribs])
                # Dedupe again
                a = np.minimum(edges[:, 0], edges[:, 1])
                b = np.maximum(edges[:, 0], edges[:, 1])
                edges = np.stack([a, b], axis=1)
                edges = np.unique(edges, axis=0).astype(np.int32)

                if spec.max_edges and len(edges) > int(spec.max_edges):
                    rng = np.random.default_rng(int(rng_seed + i * 17 + 33))
                    idx = rng.choice(len(edges), size=int(spec.max_edges), replace=False)
                    edges = edges[idx]

        edges_arr = edges if isinstance(edges, np.ndarray) else np.asarray(edges, dtype=np.int32)
        out[spec.name] = edges_arr.astype(np.int32)
    return out

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple

import numpy as np

from .mesh_io import MeshData


@dataclass(frozen=True)
class WireframeExtractParams:
    """Parameters for extracting a view-independent wireframe from a triangle mesh."""

    crease_angle_deg: float = 35.0
    max_edges: int = 5000
    min_edges: int = 400
    extra_rib_fraction: float = 0.03  # add a few extra edges for detail
    seed: int = 1337


def _face_normals(vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
    v0 = vertices[faces[:, 0]]
    v1 = vertices[faces[:, 1]]
    v2 = vertices[faces[:, 2]]
    n = np.cross(v1 - v0, v2 - v0)
    # normalize with eps
    lens = np.linalg.norm(n, axis=1)
    lens = np.where(lens < 1e-12, 1.0, lens)
    return n / lens[:, None]


def extract_wireframe_edges(
    mesh: MeshData,
    params: WireframeExtractParams | None = None,
) -> List[Tuple[int, int]]:
    """Extract wireframe edges (as vertex index pairs) from a mesh.

    Strategy:
    - include boundary edges (open mesh edges)
    - include crease/feature edges where adjacent faces form a large angle
    - optionally add a few extra edges for "rib" detail
    - bound total edge count with a length-based decimator

    Deterministic:
    - iteration order is sorted
    - RNG uses numpy Generator seeded by params.seed
    """
    if params is None:
        params = WireframeExtractParams()

    V = mesh.vertices
    F = mesh.faces
    if len(V) == 0 or len(F) == 0:
        return []

    crease = np.deg2rad(float(params.crease_angle_deg))
    normals = _face_normals(V, F)

    # Build edge -> faces adjacency using a dict (deterministic if we sort at end).
    edge_faces: dict[Tuple[int, int], List[int]] = {}
    for fi, tri in enumerate(F):
        a, b, c = int(tri[0]), int(tri[1]), int(tri[2])
        edges = [(a, b), (b, c), (c, a)]
        for u, v in edges:
            if u > v:
                u, v = v, u
            edge_faces.setdefault((u, v), []).append(fi)

    boundary: List[Tuple[int, int]] = []
    feature: List[Tuple[int, int]] = []
    all_edges = sorted(edge_faces.keys())

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
            # non-manifold: keep it (tends to outline messy seams)
            feature.append(e)

    # Candidate is boundary ∪ feature
    cand_set = set(boundary)
    cand_set.update(feature)
    candidates = list(cand_set)

    # Add some ribs: sample from non-candidate edges.
    rng = np.random.default_rng(int(params.seed))
    if params.extra_rib_fraction > 0.0:
        others = [e for e in all_edges if e not in cand_set]
        if others:
            k = int(max(0, round(len(all_edges) * float(params.extra_rib_fraction))))
            if k > 0:
                # deterministic selection: shuffle using RNG
                idx = np.arange(len(others))
                rng.shuffle(idx)
                add = [others[i] for i in idx[:k]]
                candidates.extend(add)

    # Decimate/expand to within [min_edges, max_edges] based on edge length.
    max_edges = int(params.max_edges)
    min_edges = int(params.min_edges)

    if len(candidates) == 0:
        candidates = all_edges

    def edge_len(e: Tuple[int, int]) -> float:
        a, b = e
        return float(np.linalg.norm(V[b] - V[a]))

    # Always compute lengths once
    lens = np.array([edge_len(e) for e in candidates], dtype=np.float64)

    # Keep strongest edges first
    order = np.argsort(-lens)  # descending
    if len(candidates) > max_edges:
        keep_idx = order[:max_edges]
        candidates = [candidates[int(i)] for i in keep_idx]
    elif len(candidates) < min_edges and len(all_edges) > len(candidates):
        # add more from all_edges by length
        extra = [e for e in all_edges if e not in set(candidates)]
        extra_lens = np.array([edge_len(e) for e in extra], dtype=np.float64)
        extra_order = np.argsort(-extra_lens)
        need = min_edges - len(candidates)
        add = [extra[int(i)] for i in extra_order[:need]]
        candidates.extend(add)

    # final stable order (for determinism)
    candidates = sorted(set(candidates))
    return candidates

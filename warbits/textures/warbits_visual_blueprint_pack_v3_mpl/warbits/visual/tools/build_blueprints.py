"""Build Visual Blueprint JSONL records from 3D mesh assets.

This is the *asset ingest step* for the Visual Blueprint system.

Supported inputs (best -> worst):
  - .glb / .gltf  (recommended)
  - .obj
  - .stl / .ply

FBX and USD often require extra native dependencies (Assimp / USD SDK).
If trimesh can't load your format on your machine, convert to GLB.

Output:
  - JSONL file where each line is one Blueprint record:
    {id, kind, source, vertices, edges, lod_edges, anchors, units}

Example:
  python -m warbits.visual.tools.build_blueprints \
    --in assets/models_raw \
    --out warbits/data/normalized/visual_blueprints.jsonl \
    --kind vehicle \
    --preset aircraft

The pipeline is intentionally deterministic (seeded) so wireframes are stable.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

import numpy as np

from ..blueprint_schema import Blueprint
from ..blueprint_db import BlueprintDB
from ..mesh_io import load_any_mesh, iter_scene_meshes, scene_to_merged_mesh
from ..wireframe_extract import EdgeSpec, extract_lod_edge_sets


SUPPORTED_EXTS = {".glb", ".gltf", ".obj", ".ply", ".stl"}


def _iter_files(root: Path) -> Iterator[Path]:
    if root.is_file():
        yield root
        return
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS:
            yield p


def _default_specs_for_preset(preset: str) -> List[EdgeSpec]:
    p = (preset or "generic").lower().strip()

    # These defaults aim for:
    # - Stable silhouettes
    # - Internal ribbing only at close range
    # - A capped number of edges for FPS
    if p in ("aircraft", "jet", "helicopter"):
        return [
            EdgeSpec(
                name="base",
                keep_hard_edges=True,
                include_all_edges=False,
                include_ribs=False,
                hard_edge_angle_deg=25.0,
                vertex_merge_eps=0.01,
                vertex_quantization=0.0,
                max_edges=4500,
                seed=7,
            ),
            EdgeSpec(
                name="lod0",
                keep_hard_edges=True,
                include_all_edges=False,
                include_ribs=True,
                rib_slices=14,
                hard_edge_angle_deg=28.0,
                vertex_merge_eps=0.01,
                vertex_quantization=0.0,
                max_edges=9000,
                seed=7,
            ),
            EdgeSpec(
                name="lod1",
                keep_hard_edges=True,
                include_all_edges=False,
                include_ribs=True,
                rib_slices=8,
                hard_edge_angle_deg=30.0,
                vertex_merge_eps=0.01,
                vertex_quantization=0.0,
                max_edges=5500,
                seed=7,
            ),
        ]

    if p in ("ground", "tank", "apc", "ifv", "spaa", "sam"):
        return [
            EdgeSpec(
                name="base",
                keep_hard_edges=True,
                include_all_edges=False,
                include_ribs=False,
                hard_edge_angle_deg=35.0,
                vertex_merge_eps=0.01,
                vertex_quantization=0.0,
                max_edges=4200,
                seed=7,
            ),
            EdgeSpec(
                name="lod0",
                keep_hard_edges=True,
                include_all_edges=False,
                include_ribs=True,
                rib_slices=10,
                hard_edge_angle_deg=40.0,
                vertex_merge_eps=0.01,
                vertex_quantization=0.0,
                max_edges=8000,
                seed=7,
            ),
            EdgeSpec(
                name="lod1",
                keep_hard_edges=True,
                include_all_edges=False,
                include_ribs=True,
                rib_slices=6,
                hard_edge_angle_deg=45.0,
                vertex_merge_eps=0.01,
                vertex_quantization=0.0,
                max_edges=5200,
                seed=7,
            ),
        ]

    # Weapons / missiles / bombs:
    if p in ("weapon", "missile", "rocket", "bomb", "shell"):
        return [
            EdgeSpec(
                name="base",
                keep_hard_edges=True,
                include_all_edges=False,
                include_ribs=False,
                hard_edge_angle_deg=25.0,
                vertex_merge_eps=0.005,
                vertex_quantization=0.0,
                max_edges=2200,
                seed=7,
            ),
            EdgeSpec(
                name="lod0",
                keep_hard_edges=True,
                include_all_edges=False,
                include_ribs=True,
                rib_slices=10,
                hard_edge_angle_deg=30.0,
                vertex_merge_eps=0.005,
                vertex_quantization=0.0,
                max_edges=3600,
                seed=7,
            ),
        ]

    # Generic fallback
    return [
        EdgeSpec(
            name="base",
            keep_hard_edges=True,
            include_all_edges=False,
            include_ribs=False,
            hard_edge_angle_deg=30.0,
            vertex_merge_eps=0.01,
            vertex_quantization=0.0,
            max_edges=4000,
            seed=7,
        ),
        EdgeSpec(
            name="lod0",
            keep_hard_edges=True,
            include_all_edges=False,
            include_ribs=True,
            rib_slices=10,
            hard_edge_angle_deg=35.0,
            vertex_merge_eps=0.01,
            vertex_quantization=0.0,
            max_edges=7000,
            seed=7,
        ),
    ]


def _anchors_from_vertices(V: np.ndarray) -> Dict[str, List[float]]:
    """Compute generic anchors from bbox. This is a good default for attachments."""
    V = np.asarray(V, dtype=float)
    if V.ndim != 2 or V.shape[1] != 3:
        raise ValueError("V must be (N,3)")
    mins = V.min(axis=0)
    maxs = V.max(axis=0)
    ctr = 0.5 * (mins + maxs)

    # WarBits convention (recommended):
    # x forward, y left, z up
    anchors = {
        "center": ctr.tolist(),
        "nose": [float(maxs[0]), float(ctr[1]), float(ctr[2])],
        "tail": [float(mins[0]), float(ctr[1]), float(ctr[2])],
        "left": [float(ctr[0]), float(maxs[1]), float(ctr[2])],
        "right": [float(ctr[0]), float(mins[1]), float(ctr[2])],
        "top": [float(ctr[0]), float(ctr[1]), float(maxs[2])],
        "bottom": [float(ctr[0]), float(ctr[1]), float(mins[2])],
    }
    return anchors


def _record_id_for_path(p: Path, *, prefix: str = "") -> str:
    # Normalize to a stable id: "folder_name/file_name" -> "folder_name__file_name"
    stem = p.stem.strip().replace(" ", "_")
    parent = p.parent.name.strip().replace(" ", "_")
    rid = f"{parent}__{stem}" if parent else stem
    if prefix:
        rid = f"{prefix.strip()}__{rid}"
    return rid.lower()


def build_blueprints_from_path(
    in_path: Path,
    *,
    kind: str,
    preset: str,
    id_prefix: str = "",
) -> List[Blueprint]:
    specs = _default_specs_for_preset(preset)
    out: List[Blueprint] = []

    for fp in _iter_files(in_path):
        obj = load_any_mesh(fp, force_scene=True)
        # trimesh returns Scene for multi-mesh; merge unless user wants separate
        meshes = []
        if hasattr(obj, "geometry"):
            # Scene
            for name, mesh in iter_scene_meshes(obj):
                meshes.append((name, mesh))
        else:
            meshes.append((fp.stem, obj))

        if not meshes:
            continue

        # For now: merge geometries into one blueprint per file.
        # Later we can support per-submesh (turret vs hull, etc).
        if len(meshes) > 1 and hasattr(obj, "geometry"):
            mesh = scene_to_merged_mesh(obj)
            meshes = [(fp.stem, mesh)]

        for name, mesh in meshes:
            V, lod_sets = extract_lod_edge_sets(mesh, specs)

            base_edges = lod_sets.get("base")
            if base_edges is None:
                # If specs didn't include base, fall back to first item
                any_name = next(iter(lod_sets.keys()))
                base_edges = lod_sets[any_name]

            lod_edges = {k: v.tolist() for k, v in lod_sets.items() if k != "base" and v is not None}

            bp = Blueprint(
                id=_record_id_for_path(fp, prefix=id_prefix),
                kind=kind,
                source=str(fp),
                units="m",
                vertices=V.tolist(),
                edges=base_edges.tolist(),
                lod_edges=lod_edges,
                anchors=_anchors_from_vertices(V),
                meta={
                    "preset": preset,
                    "mesh_name": str(name),
                    "src_ext": fp.suffix.lower(),
                    "edge_counts": {k: int(v.shape[0]) for k, v in lod_sets.items()},
                },
            )
            out.append(bp)

    return out


def _parse_args(argv: Optional[Sequence[str]] = None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_path", required=True, help="Input file or folder of meshes")
    ap.add_argument("--out", dest="out_path", required=True, help="Output JSONL path")
    ap.add_argument("--kind", default="vehicle", help="Blueprint kind (vehicle, weapon, terrain, ...)")
    ap.add_argument("--preset", default="generic", help="Extraction preset (aircraft, ground, weapon, generic)")
    ap.add_argument("--id-prefix", default="", help="Optional prefix for ids (ex: wt)")
    return ap.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    in_path = Path(args.in_path)
    out_path = Path(args.out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    blueprints = build_blueprints_from_path(
        in_path,
        kind=str(args.kind),
        preset=str(args.preset),
        id_prefix=str(args.id_prefix),
    )

    # Append or overwrite? For now: overwrite.
    with out_path.open("w", encoding="utf-8") as f:
        for bp in blueprints:
            f.write(json.dumps(bp.to_json(), ensure_ascii=False) + "\n")

    print(f"Wrote {len(blueprints)} blueprints -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

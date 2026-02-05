from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any, Iterable, List, Tuple, cast

import numpy as np

from warbits.visual.blueprint_db import write_blueprints_jsonl
from warbits.visual.blueprint_schema import Blueprint
from warbits.visual.mesh_io import center_vertices, iter_scene_meshes, load_any_mesh, scene_to_merged_mesh
from warbits.visual.wireframe_extract import LODSpec, extract_lod_edge_sets


ASSET_EXTS = {".obj", ".glb", ".gltf"}


def _slug(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9_\-:.]+", "_", s)
    s = re.sub(r"_+", "_", s)
    return s.strip("_")


def _default_lod_specs(preset: str) -> Tuple[LODSpec, ...]:
    preset = preset.lower().strip()
    if preset == "quality":
        return (
            LODSpec(name="lod0", feature_angle_deg=15.0, max_edges=12000, sample_rate=1.0, include_boundary=True, include_ribs=True, ribs_slices=10),
            LODSpec(name="lod1", feature_angle_deg=30.0, max_edges=6000, sample_rate=1.0, include_boundary=True, include_ribs=False),
            LODSpec(name="lod2", feature_angle_deg=55.0, max_edges=2500, sample_rate=1.0, include_boundary=True, include_ribs=False),
        )
    if preset == "fast":
        return (
            LODSpec(name="lod0", feature_angle_deg=25.0, max_edges=5000, sample_rate=1.0, include_boundary=True, include_ribs=False),
            LODSpec(name="lod1", feature_angle_deg=45.0, max_edges=2500, sample_rate=1.0, include_boundary=True, include_ribs=False),
            LODSpec(name="lod2", feature_angle_deg=65.0, max_edges=1000, sample_rate=1.0, include_boundary=True, include_ribs=False),
        )
    # balanced
    return (
        LODSpec(name="lod0", feature_angle_deg=20.0, max_edges=8000, sample_rate=1.0, include_boundary=True, include_ribs=False),
        LODSpec(name="lod1", feature_angle_deg=35.0, max_edges=4000, sample_rate=1.0, include_boundary=True, include_ribs=False),
        LODSpec(name="lod2", feature_angle_deg=55.0, max_edges=2000, sample_rate=1.0, include_boundary=True, include_ribs=False),
    )


def _iter_assets(assets_dir: Path) -> Iterable[Path]:
    for p in sorted(assets_dir.rglob("*")):
        if p.is_file() and p.suffix.lower() in ASSET_EXTS:
            yield p


def build_blueprints_from_assets(
    assets_dir: Path,
    kind: str,
    id_prefix: str,
    preset: str,
    split_scene: bool,
    center: bool,
    rng_seed: int,
) -> List[Blueprint]:
    blueprints: List[Blueprint] = []
    lod_specs = _default_lod_specs(preset)

    for asset_path in _iter_assets(assets_dir):
        obj = load_any_mesh(asset_path, force_scene=True)
        obj_any = cast(Any, obj)

        if hasattr(obj_any, "geometry") and split_scene:
            # Scene: one blueprint per geometry
            for geom_name, geom in iter_scene_meshes(obj_any):
                bp_id = _slug(f"{id_prefix}{asset_path.stem}:{geom_name}")
                v = np.asarray(geom.vertices, dtype=np.float64)
                if center:
                    v = center_vertices(v)

                lod_edges = extract_lod_edge_sets(cast(Any, geom), lod_specs, rng_seed=rng_seed)
                # Base edges = lod0 for convenience
                edges0 = lod_edges.get("lod0", np.zeros((0, 2), dtype=np.int32))

                bp = Blueprint(
                    blueprint_id=bp_id,
                    kind=kind,
                    repr="wire3d",
                    vertices_m=[(float(x), float(y), float(z)) for x, y, z in v],
                    edges=[(int(a), int(b)) for a, b in edges0],
                    lod_edges={k: tuple((int(a), int(b)) for a, b in e) for k, e in lod_edges.items()},
                    tags=[_slug(asset_path.stem)],
                    meta={
                        "source_path": str(asset_path),
                        "source_geom": str(geom_name),
                        "preset": preset,
                    },
                )
                bp.validate()
                blueprints.append(bp)
        else:
            # Single mesh / merged scene
            mesh: Any = obj_any
            if hasattr(obj_any, "geometry") and not hasattr(obj_any, "faces"):
                mesh = scene_to_merged_mesh(obj_any)

            v = np.asarray(mesh.vertices, dtype=np.float64)
            if center:
                v = center_vertices(v)

            lod_edges = extract_lod_edge_sets(mesh, lod_specs, rng_seed=rng_seed)
            edges0 = lod_edges.get("lod0", np.zeros((0, 2), dtype=np.int32))

            bp_id = _slug(f"{id_prefix}{asset_path.stem}")
            bp = Blueprint(
                blueprint_id=bp_id,
                kind=kind,
                repr="wire3d",
                vertices_m=[(float(x), float(y), float(z)) for x, y, z in v],
                edges=[(int(a), int(b)) for a, b in edges0],
                lod_edges={k: tuple((int(a), int(b)) for a, b in e) for k, e in lod_edges.items()},
                tags=[_slug(asset_path.stem)],
                meta={
                    "source_path": str(asset_path),
                    "preset": preset,
                },
            )
            bp.validate()
            blueprints.append(bp)

    return blueprints


def main() -> int:
    ap = argparse.ArgumentParser(description="Build Visual Blueprint DB (JSONL) from mesh assets (OBJ/GLB).")
    ap.add_argument("--assets", type=str, default="assets", help="Assets directory to scan recursively for .obj/.glb/.gltf")
    ap.add_argument("--out", type=str, default="data/visual_blueprints.jsonl", help="Output JSONL path")
    ap.add_argument("--kind", type=str, default="vehicle", help="Blueprint kind label (vehicle/weapon/sensor/effect)")
    ap.add_argument("--id-prefix", type=str, default="", help="Prefix to prepend to all generated blueprint ids")
    ap.add_argument("--preset", type=str, default="balanced", choices=["fast", "balanced", "quality"], help="LOD/edge extraction preset")
    ap.add_argument("--no-split-scene", action="store_true", help="If set, merge all meshes in a scene into one blueprint")
    ap.add_argument("--no-center", action="store_true", help="If set, do not center vertices around origin")
    ap.add_argument("--seed", type=int, default=1234, help="Deterministic RNG seed for edge sampling")
    args = ap.parse_args()

    assets_dir = Path(args.assets)
    out_path = Path(args.out)

    if not assets_dir.exists():
        raise FileNotFoundError(assets_dir)

    blueprints = build_blueprints_from_assets(
        assets_dir=assets_dir,
        kind=args.kind,
        id_prefix=args.id_prefix,
        preset=args.preset,
        split_scene=not args.no_split_scene,
        center=not args.no_center,
        rng_seed=int(args.seed),
    )
    write_blueprints_jsonl(out_path, blueprints)
    print(f"Wrote {len(blueprints)} blueprints -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

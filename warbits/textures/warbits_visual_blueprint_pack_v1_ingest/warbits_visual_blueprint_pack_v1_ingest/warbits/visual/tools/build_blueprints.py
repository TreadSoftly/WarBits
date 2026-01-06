from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np

from ..blueprint_db import write_blueprints_jsonl
from ..blueprint_schema import BlueprintKind, BlueprintRecord
from ..mesh_io import MeshData, load_gltf_scene_optional, read_obj_objects
from ..wireframe_extract import WireframeExtractParams, extract_wireframe_edges


def _slug(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "unnamed"


def _iter_input_files(root: Path) -> List[Path]:
    if root.is_file():
        return [root]
    out: List[Path] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() in (".obj", ".glb", ".gltf"):
            out.append(p)
    return sorted(out)


def _load_meshes(path: Path) -> Dict[str, MeshData]:
    suf = path.suffix.lower()
    if suf == ".obj":
        return read_obj_objects(path)
    if suf in (".glb", ".gltf"):
        return load_gltf_scene_optional(path)
    raise ValueError(f"Unsupported file: {path}")


def build_blueprints(
    input_path: Path,
    out_jsonl: Path,
    kind: BlueprintKind,
    id_prefix: str,
    params: WireframeExtractParams,
) -> List[BlueprintRecord]:
    records: List[BlueprintRecord] = []

    files = _iter_input_files(input_path)
    if not files:
        raise SystemExit(f"No supported assets found under: {input_path}")

    for f in files:
        meshes = _load_meshes(f)
        if not meshes:
            continue

        for obj_name, mesh in meshes.items():
            edges = extract_wireframe_edges(mesh, params=params)

            # Note: we store raw mesh vertices; if you need scaling/orientation fixes,
            # attach them in meta now and apply later in a normalization step.
            vertices_m = mesh.vertices.astype(float).tolist()

            bp_id = f"{kind}:{id_prefix}{_slug(f.stem)}_{_slug(obj_name)}"

            rec = BlueprintRecord(
                blueprint_id=bp_id,
                kind=kind,
                vertices_m=vertices_m,
                edges=edges,
                tags=[kind],
                meta={
                    "source_file": str(f.as_posix()),
                    "source_object": obj_name,
                    "wireframe_params": {
                        "crease_angle_deg": params.crease_angle_deg,
                        "max_edges": params.max_edges,
                        "min_edges": params.min_edges,
                        "extra_rib_fraction": params.extra_rib_fraction,
                        "seed": params.seed,
                    },
                },
            )
            records.append(rec)

    write_blueprints_jsonl(out_jsonl, records)
    return records


def main() -> None:
    ap = argparse.ArgumentParser(description="Build Visual Blueprint DB (JSONL) from OBJ/GLB assets.")
    ap.add_argument("--input", required=True, help="Input file or directory containing OBJ/GLB/GLTF assets.")
    ap.add_argument("--out", required=True, help="Output JSONL path (blueprints.jsonl).")
    ap.add_argument("--kind", default="vehicle", choices=["vehicle","weapon","sensor","effect","terrain_prop"], help="Blueprint kind.")
    ap.add_argument("--id-prefix", default="", help="Optional prefix added after kind:, before slug.")
    ap.add_argument("--crease", type=float, default=35.0, help="Crease angle deg for feature edges.")
    ap.add_argument("--max-edges", type=int, default=5000, help="Max edges to keep per blueprint.")
    ap.add_argument("--min-edges", type=int, default=400, help="Min edges to keep per blueprint.")
    ap.add_argument("--rib-frac", type=float, default=0.03, help="Fraction of extra edges to add as ribs.")
    ap.add_argument("--seed", type=int, default=1337, help="Deterministic seed for rib sampling.")
    args = ap.parse_args()

    input_path = Path(args.input)
    out_path = Path(args.out)

    params = WireframeExtractParams(
        crease_angle_deg=float(args.crease),
        max_edges=int(args.max_edges),
        min_edges=int(args.min_edges),
        extra_rib_fraction=float(args.rib_frac),
        seed=int(args.seed),
    )

    records = build_blueprints(
        input_path=input_path,
        out_jsonl=out_path,
        kind=args.kind,  # type: ignore[arg-type]
        id_prefix=str(args.id_prefix),
        params=params,
    )
    print(f"Wrote {len(records)} blueprints -> {out_path}")


if __name__ == "__main__":
    main()

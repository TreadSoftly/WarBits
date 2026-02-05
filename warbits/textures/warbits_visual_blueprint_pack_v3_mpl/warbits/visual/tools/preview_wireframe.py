from __future__ import annotations

import argparse
from typing import Any, cast

import numpy as np

from warbits.visual.blueprint_db import BlueprintDB
from warbits.visual.registry import VisualRegistry


def main() -> int:
    ap = argparse.ArgumentParser(description="Preview a visual blueprint wireframe from a JSONL DB.")
    ap.add_argument("--db", type=str, required=True, help="Path to blueprints JSONL")
    ap.add_argument("--id", type=str, default="", help="Blueprint id to preview (omit to list ids)")
    ap.add_argument("--lod", type=str, default="", help="LOD name (lod0/lod1/lod2...). Omit to auto by distance.")
    ap.add_argument("--distance", type=float, default=0.0, help="Distance in meters for auto LOD selection.")
    ap.add_argument("--elev", type=float, default=20.0)
    ap.add_argument("--azim", type=float, default=-55.0)
    args = ap.parse_args()

    db = BlueprintDB.load_jsonl(args.db)
    reg = VisualRegistry(db=db)

    if not args.id:
        ids = reg.ids()
        print(f"{len(ids)} blueprints in DB:")
        for i in ids[:200]:
            print(" ", i)
        if len(ids) > 200:
            print(f"... ({len(ids)-200} more)")
        return 0

    geom = reg.geometry(args.id)
    if geom is None:
        raise SystemExit(f"Blueprint not found or not wire3d: {args.id}")

    if args.lod:
        edges = geom.edges_by_lod.get(args.lod)
        if edges is None:
            raise SystemExit(f"LOD {args.lod!r} not present for {args.id}. Available: {list(geom.edges_by_lod.keys())}")
    else:
        edges = reg.edges_for_distance(args.id, float(args.distance))
        assert edges is not None

    # Build segments
    verts = geom.vertices_m
    seg = verts[edges]  # (M,2,3)

    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Line3DCollection  # type: ignore[import-not-found]

    plt_any = cast(Any, plt)
    fig = plt_any.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection="3d")
    fig.patch.set_facecolor("black")
    ax.set_facecolor("black")

    lc = Line3DCollection(seg, colors="#39FF14", linewidths=1.2, alpha=1.0)
    ax.add_collection3d(lc)

    # Fit view
    mins = verts.min(axis=0)
    maxs = verts.max(axis=0)
    center = (mins + maxs) / 2.0
    span = float(np.max(maxs - mins))
    if span <= 1e-6:
        span = 1.0
    pad = span * 0.7
    ax.set_xlim(center[0] - pad, center[0] + pad)
    ax.set_ylim(center[1] - pad, center[1] + pad)
    ax.set_zlim(center[2] - pad, center[2] + pad)

    ax.view_init(elev=float(args.elev), azim=float(args.azim))
    ax.set_axis_off()

    title_lod = args.lod or f"auto@{args.distance:.1f}m"
    plt_any.title(f"{args.id} ({title_lod})", color="white")
    plt_any.tight_layout()
    plt_any.show()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
    raise SystemExit(main())
    raise SystemExit(main())

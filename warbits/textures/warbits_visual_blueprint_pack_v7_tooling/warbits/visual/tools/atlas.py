"""warbits.visual.tools.atlas

Generate a PNG atlas of blueprint previews.

This is meant for *offline* QA:
- do we have coverage?
- do shapes read as intended?
- are LODs reasonable?

We intentionally render via 2D projection (top/side/front/iso) so the atlas is:
- deterministic
- fast
- consistent
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional, Sequence, Tuple, cast

import numpy as np
from numpy.typing import NDArray

from warbits.visual.blueprint_db import read_blueprints_jsonl
from warbits.visual.blueprint_schema import Blueprint
from warbits.visual.budgets import normalize_lod_name, select_edges_for_lod

NDArrayFloat = NDArray[np.float64]


@dataclass(frozen=True)
class AtlasRenderStyle:
    background: str = "black"
    line_color: str = "#39FF14"  # phosphor green
    line_width: float = 1.2
    alpha: float = 0.95

    # Optional label styling
    label_color: str = "#8AFF8A"
    label_size: int = 6


def _rot_x(angle_rad: float) -> NDArrayFloat:
    c, s = math.cos(angle_rad), math.sin(angle_rad)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], dtype=float)


def _rot_z(angle_rad: float) -> NDArrayFloat:
    c, s = math.cos(angle_rad), math.sin(angle_rad)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], dtype=float)


def project(points3: NDArrayFloat, view: str) -> NDArrayFloat:
    """Project 3D points to 2D for atlas display."""
    view = view.lower().strip()
    if view == "top":
        return points3[:, [0, 1]]
    if view == "side":
        return points3[:, [0, 2]]
    if view == "front":
        return points3[:, [1, 2]]
    if view == "iso":
        # Classic isometric-ish projection: yaw -45°, pitch 30°
        R = _rot_x(math.radians(30.0)) @ _rot_z(math.radians(-45.0))
        p = (R @ points3.T).T
        return p[:, [0, 1]]
    raise ValueError(f"Unknown view: {view!r} (expected top|side|front|iso)")


def _segments_2d(points2: NDArrayFloat, edges: Sequence[Tuple[int, int]]) -> NDArrayFloat:
    segs = np.zeros((len(edges), 2, 2), dtype=float)
    for i, (a, b) in enumerate(edges):
        segs[i, 0, :] = points2[a]
        segs[i, 1, :] = points2[b]
    return segs


def load_blueprints(db_path: str | Path) -> List[Blueprint]:
    db_path = str(db_path)
    bps = read_blueprints_jsonl(db_path)
    # Sort for stable atlas order
    bps.sort(key=lambda b: (b.kind, b.blueprint_id))
    return bps


def blueprint_label(bp: Blueprint, max_len: int = 42) -> str:
    # prefer a human-readable hint if provided
    label = (bp.meta or {}).get("name") or (bp.meta or {}).get("display_name") or bp.blueprint_id
    label = str(label)
    if len(label) <= max_len:
        return label
    # keep suffix (often contains the most specific identifier)
    return "..." + label[-(max_len - 1) :]


def render_atlas(
    blueprints: Sequence[Blueprint],
    out_path: str | Path,
    *,
    view: str = "iso",
    lod: str = "lod0",
    max_items: int = 200,
    cols: int = 10,
    style: AtlasRenderStyle = AtlasRenderStyle(),
    show_labels: bool = True,
) -> Path:
    """Render atlas and write it to out_path."""
    # Local import so headless builds can still run without matplotlib.
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection

    plt = cast(Any, plt)
    LineCollection = cast(Any, LineCollection)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lod = normalize_lod_name(lod)

    items = list(blueprints)[: max_items if max_items > 0 else len(blueprints)]
    if not items:
        raise ValueError("No blueprints to render")

    rows = int(math.ceil(len(items) / float(cols)))

    # Figure size scaling: tuned for readability
    fig_w = max(6.0, cols * 1.1)
    fig_h = max(4.0, rows * 1.1)

    fig, axes = plt.subplots(rows, cols, figsize=(fig_w, fig_h), dpi=220)
    fig.patch.set_facecolor(style.background)

    # axes may be a single Axes or a 2D array
    if rows == 1 and cols == 1:
        axes_grid = np.array([[axes]])
    elif rows == 1:
        axes_grid = np.array([axes])
    elif cols == 1:
        axes_grid = np.array([[a] for a in axes])
    else:
        axes_grid = axes

    for idx, ax in enumerate(axes_grid.flat):
        ax.set_facecolor(style.background)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_aspect("equal", adjustable="box")
        ax.set_axis_off()

        if idx >= len(items):
            continue

        bp = items[idx]
        pts3 = np.asarray(bp.vertices_m, dtype=float)

        # center
        center = pts3.mean(axis=0)
        pts3 = pts3 - center

        pts2 = project(pts3, view=view)
        edges = select_edges_for_lod(bp, lod)

        segs = _segments_2d(pts2, edges)
        lc = LineCollection(cast(Any, segs), colors=style.line_color, linewidths=style.line_width, alpha=style.alpha)
        ax.add_collection(lc)

        # tight bounds with margin
        xmin, ymin = pts2.min(axis=0)
        xmax, ymax = pts2.max(axis=0)
        margin = 0.15 * max(xmax - xmin, ymax - ymin, 1e-6)
        ax.set_xlim(xmin - margin, xmax + margin)
        ax.set_ylim(ymin - margin, ymax + margin)

        if show_labels:
            label = blueprint_label(bp)
            ax.text(
                0.02,
                0.04,
                label,
                transform=ax.transAxes,
                color=style.label_color,
                fontsize=style.label_size,
                ha="left",
                va="bottom",
            )

    plt.tight_layout(pad=0.4)
    fig.savefig(out_path, facecolor=style.background)
    plt.close(fig)
    return out_path


def main(argv: Optional[Sequence[str]] = None) -> int:
    import argparse

    p = argparse.ArgumentParser(description="Generate a blueprint atlas image (grid preview).")
    p.add_argument("--db", required=True, help="Path to blueprints.jsonl")
    p.add_argument("--out", required=True, help="Output PNG path")
    p.add_argument("--view", default="iso", choices=["top", "side", "front", "iso"])
    p.add_argument("--lod", default="lod0", help="lod0/lod1/lod2/lod3 (aliases: near/mid/far)")
    p.add_argument("--max", type=int, default=200, help="Max blueprints to render")
    p.add_argument("--cols", type=int, default=10, help="Atlas columns")
    p.add_argument("--no-labels", action="store_true", help="Disable name labels")
    args = p.parse_args(argv)

    bps = load_blueprints(args.db)
    render_atlas(
        bps,
        args.out,
        view=args.view,
        lod=args.lod,
        max_items=args.max,
        cols=args.cols,
        show_labels=(not args.no_labels),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

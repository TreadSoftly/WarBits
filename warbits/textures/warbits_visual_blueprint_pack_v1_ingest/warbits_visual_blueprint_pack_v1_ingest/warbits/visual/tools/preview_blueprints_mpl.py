from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, List, Tuple, TypeAlias, cast

import matplotlib.pyplot as plt  # type: ignore
import numpy as np
from mpl_toolkits.mplot3d.art3d import Line3DCollection  # type: ignore
from numpy.typing import NDArray

from ..blueprint_db import read_blueprints_jsonl

FloatArray: TypeAlias = NDArray[np.float64]


def _terrain(n: int = 70, scale: float = 60.0, height: float = 4.0) -> Tuple[FloatArray, FloatArray, FloatArray]:
    x = np.linspace(-scale, scale, n)
    y = np.linspace(-scale, scale, n)
    X, Y = np.meshgrid(x, y)
    Z = (
        0.55 * np.sin(X / 6.5) * np.cos(Y / 7.0) + 0.35 * np.sin((X + Y) / 9.0) + 0.25 * np.cos((X - 1.7 * Y) / 11.0)
    ) * height
    return X, Y, Z


def _add_edges(
    ax: Any, V: FloatArray, edges: List[Tuple[int, int]], color: str = "#39FF14", lw: float = 1.4, alpha: float = 1.0
):
    segs: list[Any] = []
    for a, b in edges:
        segs.append([V[a], V[b]])
    lc = Line3DCollection(cast(Any, segs), colors=color, linewidths=lw, alpha=alpha)
    ax.add_collection3d(lc)


def main() -> None:
    ap = argparse.ArgumentParser(description="Preview a blueprint JSONL in Matplotlib.")
    ap.add_argument("--db", required=True, help="Path to blueprints.jsonl")
    ap.add_argument("--id", default="", help="Blueprint ID to render. If empty, renders first.")
    ap.add_argument("--no-terrain", action="store_true", help="Disable terrain wireframe.")
    ap.add_argument("--azim", type=float, default=-55.0)
    ap.add_argument("--elev", type=float, default=20.0)
    args = ap.parse_args()

    recs = read_blueprints_jsonl(Path(args.db))
    if not recs:
        raise SystemExit("No blueprints found.")

    rec = recs[0]
    if args.id:
        for r in recs:
            if r.blueprint_id == args.id:
                rec = r
                break

    V = np.asarray(rec.vertices_m, dtype=float)
    edges = rec.edges

    fig = cast(Any, plt).figure(figsize=(10, 7))
    ax: Any = fig.add_subplot(111, projection="3d")
    fig.patch.set_facecolor("black")
    ax.set_facecolor("black")

    if not args.no_terrain:
        X, Y, Z = _terrain()
        ax.plot_wireframe(X, Y, Z, rstride=4, cstride=4, linewidth=0.6, alpha=0.22)

    _add_edges(ax, V, edges, lw=1.6, alpha=1.0)

    # Fit camera
    mn = V.min(axis=0)
    mx = V.max(axis=0)
    ctr = 0.5 * (mn + mx)
    span = float(np.max(mx - mn) + 1e-6)
    pad = span * 1.5
    ax.set_xlim(ctr[0] - pad, ctr[0] + pad)
    ax.set_ylim(ctr[1] - pad, ctr[1] + pad)
    ax.set_zlim(ctr[2] - pad * 0.5, ctr[2] + pad * 0.8)

    ax.view_init(elev=float(args.elev), azim=float(args.azim))
    ax.set_axis_off()

    cast(Any, plt).tight_layout()
    cast(Any, plt).show()


if __name__ == "__main__":
    main()

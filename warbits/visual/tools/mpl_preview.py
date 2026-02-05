"""Standalone preview tool for Visual Blueprints in Matplotlib.

Examples:
  python -m warbits.visual.tools.mpl_preview --db data/visual_blueprints.jsonl --id f-16
  python -m warbits.visual.tools.mpl_preview --db data/visual_blueprints.jsonl --id tank_m1a2 --save out.png
"""

from __future__ import annotations

import argparse
import math
import sys
from typing import Any, Optional, Sequence, cast

import matplotlib.pyplot as plt

from ..blueprint_db import BlueprintDB
from ..lod import LODPolicy
from ..mpl.blueprint_layer import BlueprintInstance, MPLBlueprintLayer, rot_from_yaw_pitch_roll
from ..mpl.style import apply_mpl_dark_theme, neon_green_style
from ..registry import BlueprintRegistry


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, help="Path to a visual blueprints JSONL file")
    ap.add_argument("--id", required=True, help="Blueprint id to preview")
    ap.add_argument("--save", default="", help="Optional path to save a PNG instead of opening a window")
    ap.add_argument("--spin", action="store_true", help="Spin the model (simple animation)")
    ap.add_argument("--frames", type=int, default=240, help="Frames to render when --spin and --save")
    ap.add_argument("--elev", type=float, default=18.0)
    ap.add_argument("--azim", type=float, default=-55.0)
    ap.add_argument("--dist", type=float, default=60.0, help="Axis limits distance")
    return ap.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)

    db = BlueprintDB.load_jsonl(args.db)
    registry = BlueprintRegistry(
        db,
        lod_policy=LODPolicy(thresholds_m=(800.0, 2400.0), lod_names=("lod0", "lod1", "lod2")),
    )

    plt_any = cast(Any, plt)
    fig = plt_any.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection="3d")
    cast(Any, apply_mpl_dark_theme)(fig, ax)
    ax.view_init(elev=args.elev, azim=args.azim)

    d = float(args.dist)
    ax.set_xlim(-d, d)
    ax.set_ylim(-d, d)
    ax.set_zlim(-d * 0.35, d * 0.35)

    layer = MPLBlueprintLayer(ax, registry, style=neon_green_style(), enable_detail=True)

    def render_frame(theta: float) -> None:
        R = cast(Any, rot_from_yaw_pitch_roll)(theta, 0.0, 0.0)
        inst = BlueprintInstance(blueprint_id=args.id, position_m=(0.0, 0.0, 0.0), rotation_mat=R, role="friendly")
        layer.update([inst], camera_pos=(0.0, 0.0, 0.0))

    if args.spin and args.save:
        for i in range(max(1, int(args.frames))):
            theta = 2.0 * math.pi * (i / max(1, int(args.frames)))
            render_frame(theta)
        fig.savefig(args.save, dpi=180)
        print(f"Saved: {args.save}")
        return 0

    if args.spin:
        # interactive spin animation
        import matplotlib.animation as animation

        def _update(i: int) -> list[Any]:
            theta = 2.0 * math.pi * (i / 240.0)
            render_frame(theta)
            return []

        ani_any = cast(Any, animation)
        _ = ani_any.FuncAnimation(fig, _update, frames=args.frames, interval=33, blit=False)
        plt_any.show()
        return 0

    render_frame(0.0)

    if args.save:
        fig.savefig(args.save, dpi=180)
        print(f"Saved: {args.save}")
        return 0

    plt_any.show()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
    raise SystemExit(main())

from __future__ import annotations

import argparse
import math
from typing import Any

from warbits.visual.blueprint_db import BlueprintDB
from warbits.visual.panda3d.blueprint_layer import BlueprintInstance, BlueprintP3DLayer
from warbits.visual.panda3d.imports import Panda3DNotInstalled, require_panda3d
from warbits.visual.panda3d.pixel_pipeline import PixelateConfig, PixelatePipeline
from warbits.visual.panda3d.style import NEON_GREEN
from warbits.visual.registry import VisualRegistry


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Preview a wireframe blueprint in Panda3D (optional dependency).")

    p.add_argument("--blueprints", type=str, required=True, help="Path to blueprint JSONL")
    p.add_argument("--id", type=str, default=None, help="Blueprint id to preview (default: first in DB)")
    p.add_argument("--pixel", action="store_true", help="Enable low-res pixel pipeline")
    p.add_argument("--w", type=int, default=640, help="Pixel buffer width (only with --pixel)")
    p.add_argument("--h", type=int, default=360, help="Pixel buffer height (only with --pixel)")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    try:
        _p3d, ShowBase = require_panda3d()
    except Panda3DNotInstalled as e:
        raise SystemExit(str(e))

    db = BlueprintDB.load_jsonl(args.blueprints)
    registry = VisualRegistry(db)

    bp_id = args.id
    if bp_id is None:
        ids = registry.ids()
        if not ids:
            raise SystemExit("No blueprints in DB")
        bp_id = ids[0]

    base = ShowBase()
    base.disableMouse()

    # Background black
    base.setBackgroundColor(0, 0, 0, 1)

    # Basic camera setup
    base.camera.setPos(0, -40, 10)
    base.camera.lookAt(0, 0, 0)

    layer = BlueprintP3DLayer(registry, max_segments=200_000, style=NEON_GREEN)
    layer.nodepath.reparentTo(base.render)

    if args.pixel:
        PixelatePipeline(base, PixelateConfig(width=args.w, height=args.h)).enable()

    t = {"ang": 0.0}

    def update(task: Any):
        # Rotate slowly around Z
        dt = float(getattr(task, "dt", 0.0))
        t["ang"] += 0.6 * dt
        ang = t["ang"]

        c = math.cos(ang)
        s = math.sin(ang)
        rot = (
            (c, -s, 0.0),
            (s, c, 0.0),
            (0.0, 0.0, 1.0),
        )

        layer.render(
            camera_pos_m=(0.0, -40.0, 10.0),
            instances=[
                BlueprintInstance(
                    blueprint_id=bp_id,
                    position_m=(0.0, 0.0, 0.0),
                    rotation_m=rot,
                    scale=1.0,
                )
            ],
        )
        return task.cont

    base.taskMgr.add(update, "update_blueprint")
    base.run()


if __name__ == "__main__":
    main()
    main()

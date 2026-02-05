from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

import numpy as np
from numpy.typing import NDArray

from ..anchors import AnchorDB, AnchorRecord, compute_default_anchors, merge_anchor_maps
from ..blueprint_db import BlueprintDB


def _parse_vec3(s: str) -> NDArray[np.float_]:
    parts = [p.strip() for p in s.replace(",", " ").split()]
    if len(parts) != 3:
        raise ValueError("Expected 3 numbers, like '1 2 3' or '1,2,3'")
    return np.array([float(parts[0]), float(parts[1]), float(parts[2])], dtype=float)


def cmd_build(args: argparse.Namespace) -> int:
    bp_path = Path(args.blueprints)
    out_path = Path(args.anchors_out)

    db = BlueprintDB.load_jsonl(bp_path)

    existing = AnchorDB.load_jsonl(args.merge_existing) if args.merge_existing else AnchorDB()

    out = AnchorDB()

    for bid in sorted(db.ids()):
        bp = db.get(bid)
        if bp is None:
            continue

        defaults = compute_default_anchors(
            blueprint_id=bid,
            vertices_m=np.asarray(bp.vertices_m, dtype=float),
            kind_hint=None,
            meta_kind=getattr(bp.meta, "kind", None),
        )

        rec_old = existing.get(bid)
        if rec_old is None:
            out.upsert(AnchorRecord(blueprint_id=bid, anchors=defaults, kind_hint=None))
        else:
            merged = merge_anchor_maps(defaults, rec_old.anchors)
            out.upsert(AnchorRecord(blueprint_id=bid, anchors=merged, kind_hint=rec_old.kind_hint))

    out.save_jsonl(out_path)
    print(f"Wrote anchors for {len(out.blueprint_ids())} blueprints -> {out_path}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    bp_path = Path(args.blueprints)
    db = BlueprintDB.load_jsonl(bp_path)

    bid = args.blueprint_id
    bp = db.get(bid)
    if bp is None:
        print(f"Unknown blueprint_id: {bid}", file=sys.stderr)
        return 2

    anchors_override = AnchorDB.load_jsonl(args.anchors) if args.anchors else AnchorDB()
    rec = anchors_override.get(bid)

    defaults = compute_default_anchors(
        blueprint_id=bid,
        vertices_m=np.asarray(bp.vertices_m, dtype=float),
        kind_hint=rec.kind_hint if rec else None,
        meta_kind=getattr(bp.meta, "kind", None),
    )
    if rec:
        anchors = merge_anchor_maps(defaults, rec.anchors)
    else:
        anchors = defaults

    print(f"blueprint_id: {bid}")
    for name in sorted(anchors.keys()):
        v = anchors[name]
        print(f"  {name:20s}  {v[0]: .3f} {v[1]: .3f} {v[2]: .3f}")
    return 0


def cmd_set(args: argparse.Namespace) -> int:
    anchors_path = Path(args.anchors)
    db = AnchorDB.load_jsonl(anchors_path)

    bid = args.blueprint_id
    name = args.anchor_name
    vec = _parse_vec3(args.vec3)

    rec = db.get(bid)
    if rec is None:
        db.upsert(AnchorRecord(blueprint_id=bid, anchors={name: vec}, kind_hint=args.kind_hint))
    else:
        anchors = dict(rec.anchors)
        anchors[name] = vec
        kind_hint = args.kind_hint if args.kind_hint else rec.kind_hint
        db.upsert(AnchorRecord(blueprint_id=bid, anchors=anchors, kind_hint=kind_hint))

    db.save_jsonl(anchors_path)
    print(f"Set {bid}.{name} -> {vec.tolist()} in {anchors_path}")
    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    anchors_path = Path(args.anchors)
    db = AnchorDB.load_jsonl(anchors_path)

    bid = args.blueprint_id
    name = args.anchor_name

    rec = db.get(bid)
    if rec is None:
        print(f"No record for blueprint_id={bid}", file=sys.stderr)
        return 2

    anchors = dict(rec.anchors)
    if name not in anchors:
        print(f"No anchor '{name}' in blueprint_id={bid}", file=sys.stderr)
        return 2

    anchors.pop(name)
    db.upsert(AnchorRecord(blueprint_id=bid, anchors=anchors, kind_hint=rec.kind_hint))
    db.save_jsonl(anchors_path)
    print(f"Deleted {bid}.{name} from {anchors_path}")
    return 0


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="warbits.visual.anchors",
        description="Anchor authoring and auto-generation for visual blueprints (JSONL).",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    p_build = sub.add_parser("build", help="Auto-generate anchor file for all blueprints.")
    p_build.add_argument("--blueprints", required=True, help="Path to blueprint DB jsonl")
    p_build.add_argument("--anchors-out", required=True, help="Output anchors jsonl path")
    p_build.add_argument("--merge-existing", default=None, help="Existing anchors jsonl to preserve overrides")
    p_build.set_defaults(func=cmd_build)

    p_show = sub.add_parser("show", help="Show merged anchors for one blueprint_id.")
    p_show.add_argument("--blueprints", required=True, help="Path to blueprint DB jsonl")
    p_show.add_argument("--anchors", default=None, help="Anchors jsonl path (overrides)")
    p_show.add_argument("blueprint_id", help="Blueprint id")
    p_show.set_defaults(func=cmd_show)

    p_set = sub.add_parser("set", help="Set/override one anchor for a blueprint_id.")
    p_set.add_argument("--anchors", required=True, help="Anchors jsonl to edit/create")
    p_set.add_argument("--kind-hint", default=None, help="Optional kind hint for this blueprint record")
    p_set.add_argument("blueprint_id")
    p_set.add_argument("anchor_name")
    p_set.add_argument("vec3", help="Vector 'x y z' or 'x,y,z' in local blueprint meters")
    p_set.set_defaults(func=cmd_set)

    p_del = sub.add_parser("delete", help="Delete one anchor from a blueprint_id record.")
    p_del.add_argument("--anchors", required=True, help="Anchors jsonl to edit")
    p_del.add_argument("blueprint_id")
    p_del.add_argument("anchor_name")
    p_del.set_defaults(func=cmd_delete)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    p = build_argparser()
    args = p.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
    raise SystemExit(main())

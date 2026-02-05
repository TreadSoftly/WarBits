"""CLI: Build a VisualMap for your current data set.

Typical use:
  python -m warbits.visual.tools.build_visual_map \
    --data-dir warbits/data \
    --blueprints warbits/visual/assets/blueprints.jsonl \
    --overrides warbits/visual/assets/visual_overrides.json \
    --out warbits/visual/assets/visual_map.json

This is NOT required at runtime, but it makes runtime rendering faster because
the engine can load a single JSON blob instead of running heuristics.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Mapping, Optional, cast

from warbits.visual.blueprint_db import BlueprintDB
from warbits.visual.mapping.build_map import build_visual_map
from warbits.visual.mapping.overrides import load_overrides


def _load_store_from_json_dir(data_dir: Path):
    """Best-effort loader.

    If warbits.data.store.DataStore is present and has a suitable loader, we use it.
    Otherwise we load raw JSON files into a minimal SimpleNamespace.
    """

    try:
        from warbits.data.store import DataStore  # type: ignore

        # Common patterns we've used across packs.
        if hasattr(DataStore, "load_from_json_dir"):
            return DataStore.load_from_json_dir(str(data_dir))  # type: ignore
        if hasattr(DataStore, "from_json_dir"):
            return DataStore.from_json_dir(str(data_dir))  # type: ignore

        # Fallback: instantiate and then call load.
        store = DataStore()  # type: ignore
        if hasattr(store, "load_from_json_dir"):
            store.load_from_json_dir(str(data_dir))  # type: ignore
            return store

    except Exception:
        pass

    def _load(p: Path) -> Any:
        if not p.exists():
            return {}
        return json.loads(p.read_text(encoding="utf-8"))

    vehicles = _load(data_dir / "vehicles.json")
    weapons = _load(data_dir / "weapons.json")
    warheads = _load(data_dir / "warheads.json")
    sensors = _load(data_dir / "sensors.json")

    # The build_map module is permissive: it can work with dicts on these attrs.
    return SimpleNamespace(
        vehicles=_as_id_dict(vehicles, id_key="vehicle_id"),
        weapons=_as_id_dict(weapons, id_key="weapon_id"),
        warheads=_as_id_dict(warheads, id_key="warhead_id"),
        sensors=_as_id_dict(sensors, id_key="sensor_id"),
    )


def _as_id_dict(obj: Any, id_key: str) -> Dict[str, Any]:
    if isinstance(obj, dict):
        # already keyed
        obj_map = cast(Mapping[object, object], obj)
        return {str(k): v for k, v in obj_map.items()}
    if isinstance(obj, list):
        out: Dict[str, Any] = {}
        for row in cast(list[object], obj):
            if not isinstance(row, dict):
                continue
            row_map = cast(Mapping[str, Any], row)
            if id_key in row_map:
                out[str(row_map[id_key])] = dict(row_map)
        return out
    return {}


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Build WarBits visual map")
    ap.add_argument("--data-dir", type=str, default="warbits/data", help="Path to compiled data JSON directory")
    ap.add_argument("--blueprints", type=str, default=None, help="Path to blueprints.jsonl (optional)")
    ap.add_argument("--overrides", type=str, default=None, help="Path to visual overrides JSON/JSONL")
    ap.add_argument("--out", type=str, default="warbits/visual/assets/visual_map.json", help="Output JSON path")
    ap.add_argument("--out-jsonl", type=str, default=None, help="Optional JSONL output path")
    ap.add_argument(
        "--kind", type=str, default="all", choices=["all", "vehicle", "weapon"], help="Which entity kinds to map"
    )
    args = ap.parse_args(argv)

    data_dir = Path(args.data_dir)
    store = _load_store_from_json_dir(data_dir)

    blueprint_db: Optional[BlueprintDB] = None
    if args.blueprints:
        blueprint_db = BlueprintDB.load_jsonl(Path(args.blueprints))

    overrides = load_overrides(Path(args.overrides)) if args.overrides else {}

    kinds = None if args.kind == "all" else (args.kind,)
    vmap = build_visual_map(store=store, blueprints=blueprint_db, overrides=overrides, kinds=kinds)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    vmap.write_json(out_path)

    if args.out_jsonl:
        out_jsonl = Path(args.out_jsonl)
        out_jsonl.parent.mkdir(parents=True, exist_ok=True)
        vmap.write_jsonl(out_jsonl)

    print(f"Wrote {len(vmap)} bindings to: {out_path}")
    if args.out_jsonl:
        print(f"Wrote JSONL to: {args.out_jsonl}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

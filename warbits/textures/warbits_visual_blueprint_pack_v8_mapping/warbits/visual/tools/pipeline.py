"""warbits.visual.tools.pipeline

Single entrypoint CLI for visual blueprint tooling.

Subcommands:
- atlas:     render a PNG atlas of blueprint previews
- report:    write metrics + budget report JSON
- validate:  budget check, print offenders, non-zero exit if fail
- map:       build a VisualMap (entity_id -> blueprint binding)
- suggest:   generate mapping suggestions (fuzzy match IDs -> blueprint IDs)

Examples:
    python -m warbits.visual.tools.pipeline atlas \
        --db warbits/visual/assets/blueprints.jsonl --out artifacts/atlas.png

    python -m warbits.visual.tools.pipeline map \
        --data-dir warbits/data --db warbits/visual/assets/blueprints.jsonl \
        --out warbits/visual/assets/visual_map.json

    python -m warbits.visual.tools.pipeline suggest \
        --data-dir warbits/data --db warbits/visual/assets/blueprints.jsonl \
        --out artifacts/visual_bindings_suggestions.jsonl

Design notes:
- This tooling is intentionally headless (no GUI) and deterministic.
- It's safe to run in CI.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, cast


def _read_json(path: str) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _as_id_dict(obj: object, id_key: str) -> dict[str, dict[str, object]]:
    """Coerce JSON list/dict into an id->record dict."""
    if isinstance(obj, dict):
        # Either already id->rec, or wrapped.
        obj_map = cast(Mapping[object, object], obj)
        if all(isinstance(v, dict) for v in obj_map.values()):
            return {str(k): dict(cast(Mapping[str, object], v)) for k, v in obj_map.items()}
            # Maybe has "items".
            if "items" in obj and isinstance(obj["items"], list):
                obj = cast(list[object], obj["items"])
        else:
            return {}

    if isinstance(obj, list):
        out: dict[str, dict[str, object]] = {}
        for rec in cast(list[object], obj):
            if not isinstance(rec, dict):
                continue
            rec_map = cast(Mapping[str, object], rec)
            rid = rec_map.get(id_key) or rec_map.get("id") or rec_map.get("name")
            if rid is None:
                continue
            out[str(rid)] = dict(rec_map)
        return out

    return {}


def _load_store_from_json_dir(data_dir: str):
    # Prefer the repo's DataStore if available.
    try:
        from warbits.data.store import DataStore  # type: ignore

        if hasattr(DataStore, "load_from_json_dir"):
            return DataStore.load_from_json_dir(data_dir)
    except Exception:
        pass

    # Fallback: raw JSON wrapper with .vehicles/.weapons.
    vehicles_path = Path(data_dir) / "vehicles.json"
    weapons_path = Path(data_dir) / "weapons.json"

    vehicles = _as_id_dict(_read_json(str(vehicles_path)), id_key="vehicle_id") if vehicles_path.exists() else {}
    weapons = _as_id_dict(_read_json(str(weapons_path)), id_key="weapon_id") if weapons_path.exists() else {}

    class _Store:
        def __init__(self, vehicles: dict[str, dict[str, object]], weapons: dict[str, dict[str, object]]):
            self.vehicles = vehicles
            self.weapons = weapons

        def get_vehicle(self, vehicle_id: str) -> dict[str, object]:
            return self.vehicles[vehicle_id]

        def get_weapon(self, weapon_id: str) -> dict[str, object]:
            return self.weapons[weapon_id]

    return _Store(vehicles, weapons)


def cmd_atlas(args: argparse.Namespace) -> int:
    from warbits.visual.tools.atlas import load_blueprints, render_atlas

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
    print("Atlas written:", args.out)
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    from warbits.visual.tools.report import build_report, write_report

    rep = build_report(args.db, lod=args.lod)
    write_report(rep, args.out)

    summary = rep["summary"]
    print("Report written:", args.out)
    print("Total blueprints:", summary["blueprints_total"])
    print("Budget failures:", summary["budget_failures"])
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    from warbits.visual.blueprint_db import read_blueprints_jsonl
    from warbits.visual.budgets import DEFAULT_BUDGETS, check_budget, normalize_lod_name
    from warbits.visual.metrics import compute_metrics

    lod = normalize_lod_name(str(args.lod))

    bps = read_blueprints_jsonl(str(args.db))

    failures: list[tuple[Any, Any, Any]] = []
    for bp in bps:
        chk = check_budget(bp, lod=lod, budgets=DEFAULT_BUDGETS)
        if not chk.ok:
            m = compute_metrics(bp, lod=lod)
            failures.append((bp, chk, m))

    failures.sort(key=lambda t: (-t[2].edges, -t[2].vertices))

    if not failures:
        print(f"OK: all {len(bps)} blueprints pass budgets for lod={lod}")
        return 0

    print(f"FAIL: {len(failures)}/{len(bps)} blueprints exceed budgets for lod={lod}")
    print("Worst offenders (top 25):")
    for bp, chk, m in failures[:25]:
        print(f"- {bp.kind:7s} edges={m.edges:4d} verts={m.vertices:4d} id={bp.blueprint_id}")
        for reason in chk.reasons:
            print(f"    {reason}")

    # non-zero exit so CI can catch budget regressions
    return 2


def cmd_map(args: argparse.Namespace) -> int:
    from warbits.visual.blueprint_db import BlueprintDB
    from warbits.visual.mapping import build_visual_map
    from warbits.visual.mapping.overrides import load_overrides

    store = _load_store_from_json_dir(str(args.data_dir))

    db = BlueprintDB.empty()
    if args.db:
        db = BlueprintDB.load_jsonl(Path(args.db))

    overrides = load_overrides(args.overrides) if args.overrides else None

    vm = build_visual_map(store=store, blueprints=db, overrides=overrides)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    vm.write_json(out_path)

    if args.out_jsonl:
        out_jsonl = Path(args.out_jsonl)
        out_jsonl.parent.mkdir(parents=True, exist_ok=True)
        vm.write_jsonl(out_jsonl)

    print("VisualMap written:", args.out)
    if args.out_jsonl:
        print("VisualMap JSONL written:", args.out_jsonl)

    # Coverage summary
    counts: dict[str, int] = {}
    for (kind, _eid), _binding in vm.bindings.items():
        counts[kind] = counts.get(kind, 0) + 1
    for kind, n in sorted(counts.items()):
        print(f"- {kind}: {n}")

    return 0


def cmd_suggest(args: argparse.Namespace) -> int:
    from warbits.visual.blueprint_db import BlueprintDB
    from warbits.visual.mapping import best_matches

    store = _load_store_from_json_dir(str(args.data_dir))
    db = BlueprintDB.load_jsonl(Path(args.db))

    vehicle_ids = sorted(getattr(store, "vehicles", {}).keys()) if hasattr(store, "vehicles") else []
    weapon_ids = sorted(getattr(store, "weapons", {}).keys()) if hasattr(store, "weapons") else []

    blueprint_ids = sorted(db.ids())

    suggestions: list[dict[str, object]] = []
    for kind, ids in [("vehicle", vehicle_ids), ("weapon", weapon_ids)]:
        sugs = best_matches(ids, blueprint_ids, min_score=args.threshold, top_k=args.top_k)
        for s in sugs:
            suggestions.append(
                {
                    "kind": kind,
                    "entity_id": s.entity_id,
                    "blueprint_id": s.blueprint_id,
                    "score": s.score,
                }
            )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for rec in suggestions:
            f.write(json.dumps(rec, sort_keys=True) + "\n")

    print("Suggestions written:", args.out)
    print("Total suggestions:", len(suggestions))
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    import argparse

    p = argparse.ArgumentParser(description="WarBits Visual Blueprint Tooling")
    sub = p.add_subparsers(dest="cmd", required=True)

    # atlas
    pa = sub.add_parser("atlas", help="Generate blueprint atlas PNG")
    pa.add_argument("--db", required=True, help="Path to blueprints.jsonl")
    pa.add_argument("--out", required=True, help="Output PNG path")
    pa.add_argument("--view", default="iso", choices=["top", "side", "front", "iso"])
    pa.add_argument("--lod", default="lod0", help="lod0/lod1/lod2/lod3 (aliases: near/mid/far)")
    pa.add_argument("--max", type=int, default=200, help="Max blueprints to render")
    pa.add_argument("--cols", type=int, default=10, help="Atlas columns")
    pa.add_argument("--no-labels", action="store_true")
    pa.set_defaults(func=cmd_atlas)

    # report
    pr = sub.add_parser("report", help="Generate metrics/budget report JSON")
    pr.add_argument("--db", required=True, help="Path to blueprints.jsonl")
    pr.add_argument("--out", required=True, help="Output JSON path")
    pr.add_argument("--lod", default="lod0", help="lod0/lod1/lod2/lod3 (aliases: near/mid/far)")
    pr.set_defaults(func=cmd_report)

    # validate
    pv = sub.add_parser("validate", help="Validate DB against budgets")
    pv.add_argument("--db", required=True, help="Path to blueprints.jsonl")
    pv.add_argument("--lod", default="lod0", help="lod0/lod1/lod2/lod3 (aliases: near/mid/far)")
    pv.set_defaults(func=cmd_validate)

    # map
    pm = sub.add_parser("map", help="Build VisualMap (entity_id -> blueprint binding)")
    pm.add_argument("--data-dir", required=True, help="Directory containing vehicles.json/weapons.json")
    pm.add_argument("--db", default=None, help="Optional blueprints.jsonl (mesh-derived)")
    pm.add_argument("--overrides", default=None, help="Optional manual overrides JSON/JSONL")
    pm.add_argument("--out", required=True, help="Output VisualMap JSON path")
    pm.add_argument("--out-jsonl", default=None, help="Optional VisualMap JSONL path")
    pm.set_defaults(func=cmd_map)

    # suggest
    ps = sub.add_parser("suggest", help="Suggest entity_id -> blueprint_id matches")
    ps.add_argument("--data-dir", required=True, help="Directory containing vehicles.json/weapons.json")
    ps.add_argument("--db", required=True, help="blueprints.jsonl")
    ps.add_argument("--out", required=True, help="Output suggestions JSONL")
    ps.add_argument("--threshold", type=float, default=0.55)
    ps.add_argument("--top-k", type=int, default=1)
    ps.set_defaults(func=cmd_suggest)

    args = p.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from warbits.visual.qa.anchors_validate import validate_anchors_jsonl
from warbits.visual.qa.budget_validate import BudgetSpec, validate_blueprints_budgets
from warbits.visual.qa.coverage import build_coverage_report
from warbits.visual.qa.perf_scenes import run_default_perfreg
from warbits.visual.qa.provenance import check_provenance
from warbits.visual.qa.scale_validate import validate_blueprints_scale
from warbits.visual.qa.schema_validate import validate_blueprints_jsonl


def _jsonable(obj: Any) -> Any:
    if obj is None:
        return None
    if hasattr(obj, "to_json") and callable(getattr(obj, "to_json")):
        return obj.to_json()
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    return obj


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def cmd_validate(args: argparse.Namespace) -> int:
    artifacts_dir = Path(args.artifacts)
    _ensure_dir(artifacts_dir)

    schema_res = validate_blueprints_jsonl(args.blueprints, max_records=args.max_records, strict=args.strict)
    anchors_res = None
    if args.anchors:
        anchors_res = validate_anchors_jsonl(args.anchors, blueprints_jsonl_path=args.blueprints)

    budget_spec = BudgetSpec.default()
    if args.budget:
        budget_spec = BudgetSpec.from_json(args.budget)
    budgets_res = validate_blueprints_budgets(args.blueprints, budget_spec)

    scale_res = None
    if args.data_dir:
        scale_res = validate_blueprints_scale(
            args.blueprints,
            data_dir=args.data_dir,
            tol_rel=args.scale_tol,
            strict=args.strict,
        )

    ok = (
        schema_res.ok
        and (anchors_res is None or anchors_res.ok)
        and budgets_res.ok
        and (scale_res is None or scale_res.ok)
    )

    report: Dict[str, Any] = {
        "ok": ok,
        "paths": {
            "blueprints": str(args.blueprints),
            "anchors": str(args.anchors) if args.anchors else None,
            "budget": str(args.budget) if args.budget else None,
            "data_dir": str(args.data_dir) if args.data_dir else None,
        },
        "results": {
            "schema": _jsonable(schema_res),
            "anchors": _jsonable(anchors_res),
            "budgets": _jsonable(budgets_res),
            "scale": _jsonable(scale_res),
        },
    }

    out_path = artifacts_dir / (args.out_name or "validate_report.json")
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    # strict mode = fail if any errors exist
    if args.strict:
        if schema_res.errors:
            return 2
        if anchors_res is not None and anchors_res.errors:
            return 2
        if budgets_res.errors:
            return 2
        if scale_res is not None and scale_res.errors:
            return 2
    return 0


def cmd_coverage(args: argparse.Namespace) -> int:
    artifacts_dir = Path(args.artifacts)
    _ensure_dir(artifacts_dir)

    report = build_coverage_report(
        data_dir=args.data_dir,
        blueprints_jsonl=args.blueprints,
        visual_map_json=args.visual_map,
    )

    out_path = artifacts_dir / (args.out_name or "visual_coverage_report.json")
    out_path.write_text(json.dumps(report.to_json(), indent=2, sort_keys=True), encoding="utf-8")

    missing_path = artifacts_dir / (args.missing_name or "visual_missing_ids.jsonl")
    with missing_path.open("w", encoding="utf-8") as f:
        for kind, bucket in report.buckets.items():
            for mid in bucket.missing_ids:
                f.write(json.dumps({"kind": kind, "id": mid}) + "\n")

    if args.strict and any(bucket.missing_ids for bucket in report.buckets.values()):
        return 2
    return 0


def cmd_provenance(args: argparse.Namespace) -> int:
    artifacts_dir = Path(args.artifacts)
    _ensure_dir(artifacts_dir)

    rep = check_provenance(
        blueprints_jsonl_path=args.blueprints,
        provenance_path=args.provenance,
        strict=args.strict,
    )

    out_path = artifacts_dir / (args.out_name or "provenance_report.json")
    out_path.write_text(json.dumps(_jsonable(rep), indent=2, sort_keys=True), encoding="utf-8")

    if args.strict and rep.errors:
        return 2
    return 0


def cmd_perfreg(args: argparse.Namespace) -> int:
    artifacts_dir = Path(args.artifacts)
    _ensure_dir(artifacts_dir)

    out_path = artifacts_dir / (args.out_name or "perf_report.json")
    report = run_default_perfreg(
        blueprints_jsonl=args.blueprints,
        out_json=out_path,
        frames=args.frames,
        seed=args.seed,
    )

    # run_default_perfreg writes JSON; return code indicates strict threshold failures later
    _ = report
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="warbits.visual.pipeline", description="Visual Blueprint pipeline CLI (v13)")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_common_paths(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--blueprints", default="data/visual/blueprints.jsonl", help="Blueprint DB JSONL")
        sp.add_argument("--artifacts", default="artifacts", help="Output artifacts directory")

    sp = sub.add_parser("validate", help="Validate blueprint DB + anchors + budgets (+ optional scale checks)")
    add_common_paths(sp)
    sp.add_argument("--anchors", default=None, help="Anchors JSONL (optional)")
    sp.add_argument("--budget", default=None, help="Budget JSON file (optional)")
    sp.add_argument("--data-dir", default=None, help="warbits/data folder (optional; enables scale checks)")
    sp.add_argument("--scale-tol", type=float, default=0.35, help="Allowed fractional size mismatch")
    sp.add_argument("--max-records", type=int, default=None, help="Limit records for quick validation")
    sp.add_argument("--max-examples", type=int, default=25, help="Max scale warnings/examples")
    sp.add_argument("--strict", action="store_true", help="Fail on any validation error")
    sp.add_argument("--out-name", default=None, help="Override output filename")
    sp.set_defaults(func=cmd_validate)

    sp = sub.add_parser("coverage", help="Coverage report: entity IDs -> bindings -> mapped/missing")
    add_common_paths(sp)
    sp.add_argument("--data-dir", default="warbits/data", help="Data dir containing vehicles.json/weapons.json/etc")
    sp.add_argument("--visual-map", default="data/visual/visual_map.json", help="VisualMap JSON")
    sp.add_argument("--missing-name", default=None, help="Override missing ids JSONL filename")
    sp.add_argument("--strict", action="store_true", help="Fail if anything is missing")
    sp.add_argument("--out-name", default=None, help="Override output filename")
    sp.set_defaults(func=cmd_coverage)

    sp = sub.add_parser("provenance", help="Check license/provenance manifest coverage")
    add_common_paths(sp)
    sp.add_argument("--provenance", default="data/visual/provenance.jsonl", help="Provenance JSONL/JSON")
    sp.add_argument("--strict", action="store_true", help="Fail if any mesh blueprint lacks provenance")
    sp.add_argument("--out-name", default=None, help="Override output filename")
    sp.set_defaults(func=cmd_provenance)

    sp = sub.add_parser("perfreg", help="Run deterministic perf regression scenes (CPU-side)")
    add_common_paths(sp)
    sp.add_argument("--frames", type=int, default=120, help="Frames per scene")
    sp.add_argument("--seed", type=int, default=7, help="Deterministic seed")
    sp.add_argument("--out-name", default=None, help="Override output filename")
    sp.set_defaults(func=cmd_perfreg)

    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
    raise SystemExit(main())

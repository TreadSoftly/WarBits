"""warbits.visual.tools.report

Generate a metrics + budget report for a blueprint DB.

Outputs a JSON file with:
- per-blueprint metrics
- budget pass/fail per blueprint
- summary stats by kind/tag

This tool is intentionally simple so it can run anywhere (CI, dev machine).
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence

import json

from ..blueprint_db import read_blueprints_jsonl
from ..budgets import DEFAULT_BUDGETS, check_budget, infer_budget_kind, normalize_lod_name
from ..metrics import compute_metrics


def build_report(db_path: str | Path, *, lod: str = "lod0") -> Dict[str, object]:
    lod = normalize_lod_name(lod)
    blueprints = read_blueprints_jsonl(str(db_path))

    per_kind = Counter()
    per_tag = Counter()

    items: List[Dict[str, object]] = []
    failures: List[Dict[str, object]] = []

    for bp in blueprints:
        per_kind[bp.kind] += 1
        for t in (bp.tags or []):
            per_tag[t] += 1

        m = compute_metrics(bp, lod=lod)
        b = check_budget(bp, lod=lod, budgets=DEFAULT_BUDGETS)

        rec = {
            "blueprint_id": bp.blueprint_id,
            "kind": bp.kind,
            "budget_kind": infer_budget_kind(bp),
            "tags": list(bp.tags or []),
            "lod": lod,
            "metrics": m.to_dict(),
            "budget_ok": b.ok,
            "budget_reasons": list(b.reasons),
            "meta": bp.meta or {},
        }
        items.append(rec)

        if not b.ok:
            failures.append(rec)

    # Sort worst offenders first by edges, then vertices
    failures.sort(key=lambda r: (-(r["metrics"]["edges"]), -(r["metrics"]["vertices"])))

    summary = {
        "blueprints_total": len(blueprints),
        "by_kind": dict(per_kind),
        "top_tags": dict(per_tag.most_common(30)),
        "budget_failures": len(failures),
        "budget_failures_top": failures[:50],
    }

    return {
        "summary": summary,
        "items": items,
    }


def write_report(report: Mapping[str, object], out_path: str | Path) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return out_path


def main(argv: Optional[Sequence[str]] = None) -> int:
    import argparse

    p = argparse.ArgumentParser(description="Generate blueprint metrics/budget report")    
    p.add_argument("--db", required=True, help="Path to blueprints.jsonl")
    p.add_argument("--out", required=True, help="Output JSON path")
    p.add_argument("--lod", default="lod0", help="lod0/lod1/lod2/lod3 (aliases: near/mid/far)")
    args = p.parse_args(argv)

    report = build_report(args.db, lod=args.lod)
    write_report(report, args.out)

    summary = report["summary"]
    print("Blueprint report written:", args.out)
    print("Total blueprints:", summary["blueprints_total"])
    print("Budget failures:", summary["budget_failures"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

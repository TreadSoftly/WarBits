"""warbits.visual.tools.pipeline

Single entrypoint CLI for visual blueprint tooling.

Subcommands:
- atlas:    render a PNG atlas of blueprint previews
- report:   write metrics + budget report JSON
- validate: budget check, print offenders, non-zero exit if fail

Example:
    python -m warbits.visual.tools.pipeline atlas --db data/visual/blueprints.jsonl --out artifacts/atlas.png
"""

from __future__ import annotations

from typing import Any, Optional, Sequence, cast


def cmd_atlas(args: Any) -> int:
    from .atlas import load_blueprints, render_atlas  # type: ignore[reportUnknownVariableType]

    bps = cast(list[Any], load_blueprints(args.db))
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


def cmd_report(args: Any) -> int:
    from .report import build_report, write_report

    rep = build_report(args.db, lod=args.lod)
    write_report(rep, args.out)

    summary = cast(dict[str, Any], rep["summary"])
    print("Report written:", args.out)
    print("Total blueprints:", summary["blueprints_total"])
    print("Budget failures:", summary["budget_failures"])
    return 0


def cmd_validate(args: Any) -> int:
    from warbits.visual.blueprint_db import read_blueprints_jsonl

    from ..budgets import DEFAULT_BUDGETS, check_budget, normalize_lod_name  # type: ignore[reportUnknownVariableType]
    from ..metrics import compute_metrics

    lod = normalize_lod_name(args.lod)

    bps = read_blueprints_jsonl(args.db)

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

    args = p.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

if __name__ == "__main__":
    raise SystemExit(main())
    raise SystemExit(main())

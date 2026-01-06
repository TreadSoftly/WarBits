from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from warbits.data.store import DataStore
from warbits.data.validate import validate_all


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="validate_data",
        description="Validate Warbits data tables",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="optional data root (defaults to packaged warbits/data)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit JSON report",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="treat warnings as errors",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    store = DataStore(root=args.root)
    report = validate_all(store)

    if args.json:
        payload: dict[str, Any] = {
            "errors": report.error_count,
            "warnings": report.warning_count,
            "issues": [
                {
                    "table": issue.table,
                    "row": issue.row,
                    "field": issue.field,
                    "severity": issue.severity,
                    "message": issue.message,
                }
                for issue in report.issues
            ],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for issue in report.issues:
            row = f"[{issue.row}]" if issue.row is not None else ""
            print(f"{issue.severity.upper():7s} {issue.table}{row}.{issue.field}: {issue.message}")
        print(f"Errors: {report.error_count}  Warnings: {report.warning_count}")

    if report.error_count:
        return 1
    if args.strict and report.warning_count:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

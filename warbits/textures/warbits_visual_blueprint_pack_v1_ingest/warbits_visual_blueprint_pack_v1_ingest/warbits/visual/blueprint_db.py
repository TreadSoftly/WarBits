from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List

from .blueprint_schema import BlueprintRecord


def write_blueprints_jsonl(path: str | Path, records: Iterable[BlueprintRecord]) -> None:
    """Write blueprint records as JSONL.

    Determinism goals:
    - stable key ordering
    - stable float formatting (via json module)
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for r in records:
            s = json.dumps(r.to_dict(), sort_keys=True, separators=(",", ":"))
            f.write(s)
            f.write("\n")


def read_blueprints_jsonl(path: str | Path) -> List[BlueprintRecord]:
    p = Path(path)
    out: List[BlueprintRecord] = []
    with p.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                out.append(BlueprintRecord.from_dict(d))
            except Exception as e:
                raise ValueError(f"Failed parsing JSONL at line {line_no}: {e}") from e
    return out

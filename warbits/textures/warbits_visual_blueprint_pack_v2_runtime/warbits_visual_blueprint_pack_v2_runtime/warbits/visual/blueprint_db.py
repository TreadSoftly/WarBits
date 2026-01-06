from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Tuple

from .blueprint_schema import Blueprint


def read_blueprints_jsonl(path: str | Path) -> List[Blueprint]:
    """Read JSONL file into a list of Blueprint records."""
    path = Path(path)
    records: List[Blueprint] = []
    with path.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                obj = json.loads(line)
                bp = Blueprint.from_json_obj(obj)
                bp.validate()
            except Exception as e:
                raise ValueError(f"{path}:{lineno}: invalid blueprint JSONL line: {e}") from e
            records.append(bp)
    return records


def write_blueprints_jsonl(path: str | Path, records: Sequence[Blueprint]) -> None:
    """Write Blueprint records to a JSONL file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            r.validate()
            f.write(json.dumps(r.to_json_obj(), ensure_ascii=False) + "\n")


@dataclass
class BlueprintDB:
    """In-memory index of blueprints loaded from one or more JSONL files."""

    by_id: Dict[str, Blueprint]

    @staticmethod
    def empty() -> "BlueprintDB":
        return BlueprintDB(by_id={})

    @staticmethod
    def load_jsonl(path: str | Path) -> "BlueprintDB":
        by_id: Dict[str, Blueprint] = {}
        for bp in read_blueprints_jsonl(path):
            if bp.blueprint_id in by_id:
                raise ValueError(f"Duplicate blueprint id: {bp.blueprint_id}")
            by_id[bp.blueprint_id] = bp
        return BlueprintDB(by_id=by_id)

    @staticmethod
    def load_many_jsonl(paths: Sequence[str | Path]) -> "BlueprintDB":
        by_id: Dict[str, Blueprint] = {}
        for p in paths:
            sub = BlueprintDB.load_jsonl(p)
            dupes = set(by_id.keys()) & set(sub.by_id.keys())
            if dupes:
                raise ValueError(f"Duplicate blueprint ids across DB files: {sorted(dupes)[:10]} ...")
            by_id.update(sub.by_id)
        return BlueprintDB(by_id=by_id)

    # ------------------------------------------------------------------
    # Access
    # ------------------------------------------------------------------
    def get(self, blueprint_id: str) -> Optional[Blueprint]:
        return self.by_id.get(blueprint_id)

    def require(self, blueprint_id: str) -> Blueprint:
        bp = self.get(blueprint_id)
        if bp is None:
            raise KeyError(f"Blueprint not found: {blueprint_id}")
        return bp

    def ids(self) -> Tuple[str, ...]:
        return tuple(self.by_id.keys())

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def coverage_report(self, expected_ids: Iterable[str]) -> Dict[str, List[str]]:
        """Return {"present": [...], "missing": [...]} for the provided ID list."""
        present: List[str] = []
        missing: List[str] = []
        for _id in expected_ids:
            if _id in self.by_id:
                present.append(_id)
            else:
                missing.append(_id)
        return {"present": present, "missing": missing}

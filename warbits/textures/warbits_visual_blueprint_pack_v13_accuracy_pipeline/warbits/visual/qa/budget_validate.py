from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Union, cast

PathLike = Union[str, Path]


@dataclass(frozen=True)
class BudgetSpec:
    """Soft budgets for visuals.

    These are used as tripwires rather than hard caps.
    The renderer can also choose stricter per-frame budgets.
    """

    max_edges_by_lod: Dict[str, int]

    @classmethod
    def from_dict(cls, obj: Dict[str, Any]) -> "BudgetSpec":
        # Accept either {"max_edges_by_lod": {...}} or a bare {...} mapping.
        if "max_edges_by_lod" in obj and isinstance(obj.get("max_edges_by_lod"), dict):
            m = {str(k): int(v) for k, v in obj["max_edges_by_lod"].items()}
        else:
            m = {str(k): int(v) for k, v in obj.items()}
        return cls(max_edges_by_lod=m)

    @classmethod
    def from_json(cls, path: PathLike) -> "BudgetSpec":
        p = Path(path)
        obj = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(obj, dict):
            raise ValueError(f"Budget JSON must be an object, got: {type(obj)}")
        return cls.from_dict(cast(Dict[str, Any], obj))

    def to_dict(self) -> Dict[str, Any]:
        return {"max_edges_by_lod": dict(self.max_edges_by_lod)}

    @staticmethod
    def default() -> "BudgetSpec":
        return BudgetSpec(
            max_edges_by_lod={
                "lod0": 5000,
                "lod1": 2500,
                "lod2": 1200,
                "lod3": 300,
            }
        )


@dataclass
class BudgetValidationResult:
    path: str
    errors: list[str] = field(default_factory=lambda: cast(list[str], []))
    warnings: list[str] = field(default_factory=lambda: cast(list[str], []))
    total_records: int = 0
    violated_records: int = 0

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def validate_blueprints_budgets(
    blueprints_jsonl: PathLike,
    spec: Optional[BudgetSpec] = None,
) -> BudgetValidationResult:
    """Validate edge-count budgets per LOD.

    The JSONL record must contain either:
    - edges (base), and optionally lod_edges
    - or lod_edges only

    This validator does *not* care about topology correctness; schema_validate covers that.
    """

    path = str(blueprints_jsonl)
    res = BudgetValidationResult(path=path)
    if spec is None:
        spec = BudgetSpec.default()

    p = Path(blueprints_jsonl)
    if not p.exists():
        res.errors.append(f"blueprints_jsonl not found: {p}")
        return res

    for line_no, line in enumerate(p.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        res.total_records += 1
        try:
            obj = json.loads(line)
        except Exception as e:
            res.errors.append(f"{p}:{line_no}: invalid JSON: {e}")
            continue

        blueprint_id = obj.get("blueprint_id") or obj.get("id") or "<missing blueprint_id>"

        edges = obj.get("edges")
        lod_edges = obj.get("lod_edges")
        if isinstance(lod_edges, dict):
            lod_map = cast(Dict[str, Any], lod_edges)
            counts: dict[str, int] = {
                str(k): len(cast(list[Any], v)) if isinstance(v, list) else 0 for k, v in lod_map.items()
            }
        else:
            counts: dict[str, int] = {}

        if isinstance(edges, list):
            counts.setdefault("lod0", len(cast(list[Any], edges)))

        violated = False
        for lod, max_edges in spec.max_edges_by_lod.items():
            c = counts.get(lod)
            if c is None:
                continue
            if c > max_edges:
                violated = True
                res.warnings.append(f"{p}:{line_no}: {blueprint_id} exceeds budget for {lod}: {c} edges > {max_edges}")

        if violated:
            res.violated_records += 1

    return res


# Back-compat alias (older drafts used this name).
def validate_blueprint_edge_budgets(
    blueprints_jsonl_path: PathLike,
    budget: BudgetSpec,
) -> BudgetValidationResult:
    return validate_blueprints_budgets(blueprints_jsonl_path, budget)

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Set, Tuple, Union, cast


def _empty_bucket_dict() -> dict[str, "CoverageBucket"]:
    return {}


PathLike = Union[str, Path]


@dataclass
class CoverageBucket:
    total: int = 0
    mapped_mesh: int = 0
    mapped_procedural: int = 0
    missing: int = 0
    missing_ids: list[str] = field(default_factory=lambda: cast(list[str], []))

    @property
    def mapped_any(self) -> int:
        return self.mapped_mesh + self.mapped_procedural


@dataclass
class CoverageReport:
    data_dir: str
    blueprint_db: Optional[str]
    visual_map: Optional[str]
    buckets: dict[str, CoverageBucket] = field(default_factory=_empty_bucket_dict)

    @property
    def overall_total(self) -> int:
        return sum(b.total for b in self.buckets.values())

    @property
    def kinds(self) -> dict[str, CoverageBucket]:
        """Back-compat alias: some callers refer to per-kind buckets as `kinds`."""
        return self.buckets

    def to_json(self) -> dict[str, Any]:
        return {
            "data_dir": self.data_dir,
            "blueprint_db": self.blueprint_db,
            "visual_map": self.visual_map,
            "overall_total": self.overall_total,
            "kinds": {
                k: {
                    "total": v.total,
                    "mapped_mesh": v.mapped_mesh,
                    "mapped_procedural": v.mapped_procedural,
                    "missing": v.missing,
                    "missing_ids": v.missing_ids,
                }
                for k, v in self.buckets.items()
            },
        }


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _collect_ids_from_json(obj: Any, id_fields: Tuple[str, ...]) -> list[str]:
    ids: list[str] = []
    if isinstance(obj, list):
        items = cast(list[object], obj)
        for item in items:
            if isinstance(item, dict):
                item_map = cast(dict[str, Any], item)
                for f in id_fields:
                    if f in item_map and isinstance(item_map[f], str):
                        ids.append(item_map[f])
                        break
    elif isinstance(obj, dict):
        # Accept dict-of-records or dict keyed by id.
        obj_map = cast(dict[str, Any], obj)
        # If values are dict records, prefer their explicit fields.
        for k, v in obj_map.items():
            if isinstance(v, dict):
                v_map = cast(dict[str, Any], v)
                found = False
                for f in id_fields:
                    if f in v_map and isinstance(v_map[f], str):
                        ids.append(v_map[f])
                        found = True
                        break
                if not found:
                    ids.append(str(k))
            else:
                ids.append(str(k))
    return ids


def _collect_entity_ids(data_dir: Path) -> dict[str, list[str]]:
    """Collect entity ids from normalized JSON files.

    This is intentionally tolerant: it uses best-effort heuristics and never throws
    just because a file is missing.
    """

    out: dict[str, list[str]] = {}
    candidates = {
        "vehicle": ("vehicles.json", ("vehicle_id", "id", "name")),
        "weapon": ("weapons.json", ("weapon_id", "id", "name")),
        "warhead": ("warheads.json", ("warhead_id", "id", "name")),
        "sensor": ("sensors.json", ("sensor_id", "id", "name")),
        "loadout": ("loadouts.json", ("loadout_id", "id", "name")),
    }

    for kind, (fname, fields) in candidates.items():
        p = data_dir / fname
        if not p.exists():
            continue
        try:
            obj = _load_json(p)
        except Exception:
            continue
        ids = _collect_ids_from_json(obj, fields)
        if ids:
            out[kind] = ids

    return out


def _load_blueprint_ids(blueprints_jsonl: Optional[Path]) -> Set[str]:
    if blueprints_jsonl is None or not blueprints_jsonl.exists():
        return set()
    ids: Set[str] = set()
    for line in blueprints_jsonl.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        bid = obj.get("blueprint_id")
        if isinstance(bid, str):
            ids.add(bid)
    return ids


def _load_visual_bindings(map_path: Optional[Path]) -> dict[str, dict[str, Any]]:
    if map_path is None or not map_path.exists():
        return {}

    try:
        obj = _load_json(map_path)
    except Exception:
        return {}

    # Common format: {"bindings": {entity_id: {kind, blueprint_id/template_id}}}
    if isinstance(obj, dict):
        obj_map = cast(dict[str, Any], obj)
        b = obj_map.get("bindings")
        if isinstance(b, dict):
            b_map = cast(dict[str, Any], b)
            return {str(k): cast(dict[str, Any], v) for k, v in b_map.items() if isinstance(v, dict)}

    # Alternate format: list of bindings
    if isinstance(obj, list):
        out: dict[str, dict[str, Any]] = {}
        items = cast(list[object], obj)
        for item in items:
            if not isinstance(item, dict):
                continue
            item_map = cast(dict[str, Any], item)
            eid = item_map.get("entity_id") or item_map.get("id")
            if isinstance(eid, str):
                out[eid] = item_map
        return out

    return {}


def build_coverage_report(
    *,
    data_dir: PathLike,
    blueprints_jsonl: Optional[PathLike] = None,
    blueprint_db_path: Optional[PathLike] = None,
    visual_map_json: Optional[PathLike] = None,
    visual_map_path: Optional[PathLike] = None,
) -> CoverageReport:
    data_dir_p = Path(data_dir)
    bp_path = Path(blueprints_jsonl) if blueprints_jsonl else (Path(blueprint_db_path) if blueprint_db_path else None)
    map_path = Path(visual_map_json) if visual_map_json else (Path(visual_map_path) if visual_map_path else None)

    bp_ids = _load_blueprint_ids(bp_path)
    bindings = _load_visual_bindings(map_path)

    entities_by_kind = _collect_entity_ids(data_dir_p)

    buckets: dict[str, CoverageBucket] = {k: CoverageBucket() for k in entities_by_kind.keys()}

    for kind, ids in entities_by_kind.items():
        bucket = buckets.setdefault(kind, CoverageBucket())
        for eid in ids:
            bucket.total += 1
            b = bindings.get(eid)
            if not b:
                bucket.missing += 1
                bucket.missing_ids.append(eid)
                continue

            bkind = b.get("kind") or b.get("binding")
            if isinstance(bkind, str) and bkind.lower().startswith("mesh"):
                bucket.mapped_mesh += 1
                continue

            # blueprint_id present and exists in DB -> treat as mesh unless it looks procedural
            bid = b.get("blueprint_id")
            if isinstance(bid, str):
                if bid.startswith("proc:"):
                    bucket.mapped_procedural += 1
                elif bid in bp_ids:
                    bucket.mapped_mesh += 1
                else:
                    # unknown blueprint id -> still mapped, but likely broken.
                    bucket.mapped_mesh += 1
                continue

            tid = b.get("template_id") or b.get("proc") or b.get("template")
            if isinstance(tid, str):
                bucket.mapped_procedural += 1
                continue

            # binding exists but is malformed
            bucket.missing += 1
            bucket.missing_ids.append(eid)

    return CoverageReport(
        data_dir=str(data_dir_p),
        blueprint_db=str(bp_path) if bp_path else None,
        visual_map=str(map_path) if map_path else None,
        buckets=buckets,
    )

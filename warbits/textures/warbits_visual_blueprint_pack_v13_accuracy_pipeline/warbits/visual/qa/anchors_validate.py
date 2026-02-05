from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence, Tuple, Union, cast

PathLike = Union[str, Path]


def _empty_str_list() -> list[str]:
    return []


@dataclass
class AnchorsValidationResult:
    path: str
    total_records: int = 0
    valid_records: int = 0
    errors: list[str] = field(default_factory=_empty_str_list)
    warnings: list[str] = field(default_factory=_empty_str_list)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def _read_jsonl(path: PathLike) -> Iterable[Tuple[int, dict[str, Any]]]:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            s = line.strip()
            if not s:
                continue
            yield i, json.loads(s)


def _is_finite3(v: Any) -> bool:
    if not isinstance(v, (list, tuple)):
        return False
    seq = cast(Sequence[object], v)
    if len(seq) != 3:
        return False
    for x in seq:
        if not isinstance(x, (int, float)):
            return False
        if not math.isfinite(float(x)):
            return False
    return True


def _load_bounds(
    blueprints_jsonl_path: PathLike,
) -> dict[str, Tuple[Tuple[float, float, float], Tuple[float, float, float]]]:
    """Load axis-aligned bounds from blueprints.jsonl.

    Tolerant: supports vertices_m or vertices.
    """
    bounds: dict[str, Tuple[Tuple[float, float, float], Tuple[float, float, float]]] = {}
    for _, rec in _read_jsonl(blueprints_jsonl_path):
        bid = rec.get("blueprint_id") or rec.get("id")
        if not isinstance(bid, str) or not bid:
            continue
        verts = rec.get("vertices_m") if "vertices_m" in rec else rec.get("vertices")
        if not isinstance(verts, list) or not verts:
            continue
        verts_list = cast(list[Sequence[float]], verts)
        xs: list[float] = []
        ys: list[float] = []
        zs: list[float] = []
        ok = True
        for v_raw in verts_list:
            if not _is_finite3(v_raw):
                ok = False
                break
            xs.append(float(v_raw[0]))
            ys.append(float(v_raw[1]))
            zs.append(float(v_raw[2]))
        if not ok:
            continue
        bounds[bid] = ((min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs)))
    return bounds


def validate_anchors_jsonl(
    anchors_jsonl_path: PathLike,
    blueprints_jsonl_path: Optional[PathLike] = None,
    *,
    require_minimum: bool = False,
    required_anchors: Optional[Sequence[str]] = None,
) -> AnchorsValidationResult:
    """Validate anchors.jsonl.

    Expected record shape (tolerant):
      {"blueprint_id": "...", "anchors": {"name": [x,y,z], ...}}

    If blueprints_jsonl_path is given, this will also warn when anchors are far
    outside the blueprint bounds.

    Parameters
    - require_minimum: if True, require at least the anchors in required_anchors.
    - required_anchors: e.g. ["center", "nose", "tail"].

    Backward compatible keyword aliases:
    - anchors_jsonl (positional) is still accepted as anchors_jsonl_path.
    """

    res = AnchorsValidationResult(path=str(anchors_jsonl_path))
    req = list(required_anchors or ["center", "nose", "tail"])
    bounds = _load_bounds(blueprints_jsonl_path) if blueprints_jsonl_path else {}

    for lineno, rec in _read_jsonl(anchors_jsonl_path):
        res.total_records += 1
        bid = rec.get("blueprint_id") or rec.get("id")
        if not isinstance(bid, str) or not bid.strip():
            res.errors.append(f"{anchors_jsonl_path}:{lineno}: missing blueprint_id")
            continue
        anchors = rec.get("anchors")
        if not isinstance(anchors, dict):
            res.errors.append(f"{anchors_jsonl_path}:{lineno}: anchors must be an object")
            continue
        anchors_raw = cast(dict[Any, Any], anchors)

        # Minimum requirements (optional)
        if require_minimum:
            missing = [a for a in req if a not in anchors_raw]
            if missing:
                res.errors.append(
                    f"{anchors_jsonl_path}:{lineno}: blueprint_id={bid}: missing required anchors {missing}"
                )
                continue

        ok = True
        anchors_map: dict[str, Sequence[float]] = {}
        for name, val in anchors_raw.items():
            if not isinstance(name, str) or not name:
                res.errors.append(f"{anchors_jsonl_path}:{lineno}: blueprint_id={bid}: invalid anchor name")
                ok = False
                break
            if not _is_finite3(val):
                res.errors.append(
                    f"{anchors_jsonl_path}:{lineno}: blueprint_id={bid}: anchor '{name}' must be [x,y,z] finite numbers"
                )
                ok = False
                break
            anchors_map[name] = cast(Sequence[float], val)

        if not ok:
            continue

        # Bounds sanity (warn only)
        if bid in bounds:
            (mn, mx) = bounds[bid]
            for name, val in anchors_map.items():
                x, y, z = float(val[0]), float(val[1]), float(val[2])
                if (
                    x < mn[0] - 1e-3
                    or x > mx[0] + 1e-3
                    or y < mn[1] - 1e-3
                    or y > mx[1] + 1e-3
                    or z < mn[2] - 1e-3
                    or z > mx[2] + 1e-3
                ):
                    res.warnings.append(
                        f"{anchors_jsonl_path}:{lineno}: blueprint_id={bid}: anchor '{name}' outside bounds (ok if intentional)"
                    )

        res.valid_records += 1

    return res

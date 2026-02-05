from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple, TypeAlias, Union, cast

import numpy as np
from numpy.typing import NDArray

PathLike = Union[str, Path]
FloatArray: TypeAlias = NDArray[np.float64]


@dataclass(frozen=True)
class TargetDims:
    length_m: Optional[float] = None
    span_m: Optional[float] = None
    height_m: Optional[float] = None


@dataclass
class ScaleValidationResult:
    blueprints_path: str
    data_dir: Optional[str] = None
    checked: int = 0
    compared: int = 0
    warnings: list[str] = field(default_factory=lambda: cast(list[str], []))
    errors: list[str] = field(default_factory=lambda: cast(list[str], []))

    @property
    def ok(self) -> bool:
        return not self.errors


def _is_finite_number(x: Any) -> bool:
    try:
        return math.isfinite(float(x))
    except Exception:
        return False


def _read_json(path: PathLike) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _iter_jsonl(path: PathLike) -> Iterable[Tuple[int, Dict[str, Any]]]:
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if isinstance(rec, dict):
                yield i, cast(Dict[str, Any], rec)


def _coerce_vec3_list(obj: Any) -> Optional[FloatArray]:
    if obj is None:
        return None
    if not isinstance(obj, list):
        return None
    out: list[list[float]] = []
    rows = cast(list[object], obj)
    for row in rows:
        if not isinstance(row, list):
            return None
        row_seq = cast(list[Any], row)
        if len(row_seq) != 3:
            return None
        if not all(_is_finite_number(v) for v in row_seq):
            return None
        out.append([float(row_seq[0]), float(row_seq[1]), float(row_seq[2])])
    if not out:
        return None
    return np.asarray(out, dtype=np.float64)


def _bbox_dims(vertices_m: FloatArray) -> Tuple[float, float, float]:
    lo = vertices_m.min(axis=0)
    hi = vertices_m.max(axis=0)
    d = hi - lo
    return float(d[0]), float(d[1]), float(d[2])


def _extract_target_dims_from_record(rec: Dict[str, Any]) -> TargetDims:
    # Common keys we’ve seen across sources.
    candidates = {
        "length_m": ["length_m", "length", "overall_length_m", "overall_length", "len_m", "len"],
        "span_m": ["wingspan_m", "span_m", "span", "width_m", "width", "track_m", "track"],
        "height_m": ["height_m", "height", "overall_height_m", "overall_height"],
    }

    def pick(keys: list[str]) -> Optional[float]:
        for k in keys:
            if k in rec and _is_finite_number(rec[k]):
                v = float(rec[k])
                if v > 0:
                    return v
        return None

    length_m = pick(candidates["length_m"])
    span_m = pick(candidates["span_m"])
    height_m = pick(candidates["height_m"])
    return TargetDims(length_m=length_m, span_m=span_m, height_m=height_m)


def _iter_entity_records(data_dir: Path) -> Iterable[Tuple[str, Dict[str, Any]]]:
    """Yield (entity_id, record) from known compiled JSON files.

    This is intentionally tolerant: it tries multiple layouts.
    """

    def from_json_file(path: Path, id_key: str) -> Iterable[Tuple[str, Dict[str, Any]]]:
        obj = _read_json(path)
        if isinstance(obj, list):
            rows = cast(list[object], obj)
            for rec in rows:
                if isinstance(rec, dict):
                    rec_map = cast(Dict[str, Any], rec)
                    if id_key in rec_map and isinstance(rec_map[id_key], str):
                        yield rec_map[id_key], rec_map
        elif isinstance(obj, dict):
            # Sometimes it’s a mapping of id -> record.
            obj_map = cast(Dict[str, Any], obj)
            for k, v in obj_map.items():
                if isinstance(v, dict):
                    v_map = cast(Dict[str, Any], v)
                    # Prefer explicit id_key if present; else use dict key.
                    raw_id = v_map.get(id_key)
                    eid = raw_id if isinstance(raw_id, str) else k
                    yield eid, v_map

    file_specs = [
        ("vehicles.json", "vehicle_id"),
        ("weapons.json", "weapon_id"),
        ("warheads.json", "warhead_id"),
        ("sensors.json", "sensor_id"),
        ("loadouts.json", "loadout_id"),
    ]
    for fn, key in file_specs:
        p = data_dir / fn
        if p.exists():
            yield from from_json_file(p, key)


def extract_expected_dims_from_data_dir(data_dir: PathLike) -> Dict[str, TargetDims]:
    """Build {entity_id -> TargetDims} by scanning your compiled JSON data."""
    data_path = Path(data_dir)
    expected: Dict[str, TargetDims] = {}
    for eid, rec in _iter_entity_records(data_path):
        dims = _extract_target_dims_from_record(rec)
        if dims.length_m or dims.span_m or dims.height_m:
            expected[eid] = dims
    return expected


def validate_blueprint_scale(
    blueprints_jsonl: PathLike,
    data_dir: Optional[PathLike] = None,
    *,
    tol_rel: float = 0.30,
    tol_abs_m: float = 1.0,
    strict: bool = False,
) -> ScaleValidationResult:
    """Compare blueprint bbox dimensions to expected dims.

    This is a *sanity* check.
    - It does not try to auto-rotate or infer axes; it assumes your blueprint is normalized.
    - It’s meant to catch obvious scale failures (centimeters interpreted as meters, etc.).

    tol_rel: relative tolerance (30% default)
    tol_abs_m: absolute tolerance floor (meters)
    strict: if True, scale mismatches become errors; else warnings.
    """

    result = ScaleValidationResult(blueprints_path=str(blueprints_jsonl), data_dir=str(data_dir) if data_dir else None)
    expected: Dict[str, TargetDims] = {}
    if data_dir is not None:
        expected = extract_expected_dims_from_data_dir(Path(data_dir))

    for lineno, rec in _iter_jsonl(blueprints_jsonl):
        result.checked += 1
        bid = rec.get("blueprint_id") or rec.get("id")
        if not isinstance(bid, str) or not bid:
            continue
        vertices = rec.get("vertices_m") or rec.get("vertices")
        v = _coerce_vec3_list(vertices)
        if v is None:
            continue

        bbox = _bbox_dims(v)

        # Heuristic: map blueprint_id to entity_id by suffix after first ':' if present.
        entity_id = bid.split(":", 1)[1] if ":" in bid else bid
        tdims = expected.get(entity_id)
        if tdims is None:
            continue

        result.compared += 1
        for label, actual, expected_val in (
            ("length_m", bbox[0], tdims.length_m),
            ("span_m", bbox[1], tdims.span_m),
            ("height_m", bbox[2], tdims.height_m),
        ):
            if expected_val is None:
                continue
            abs_err = abs(actual - expected_val)
            rel_err = abs_err / max(1e-6, expected_val)
            if abs_err > tol_abs_m and rel_err > tol_rel:
                msg = (
                    f"{bid} scale mismatch for {label}: bbox={actual:.3f}m vs expected={expected_val:.3f}m "
                    f"(abs_err={abs_err:.3f}m rel_err={rel_err:.2%}) [line {lineno}]"
                )
                if strict:
                    result.errors.append(msg)
                else:
                    result.warnings.append(msg)

    return result


# Back-compat alias: some scripts refer to this plural form.
def validate_blueprints_scale(*args: Any, **kwargs: Any) -> ScaleValidationResult:
    return validate_blueprint_scale(*args, **kwargs)

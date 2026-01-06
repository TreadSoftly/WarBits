from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

Number = Union[int, float]
PathLike = Union[str, Path]


@dataclass
class SchemaValidationResult:
    """Result of validating a blueprint JSONL DB."""

    path: str
    total_records: int = 0
    valid_records: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def _is_finite_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and math.isfinite(float(x))


def _as_vec3_list(v: Any) -> Optional[List[List[float]]]:
    if not isinstance(v, list) or len(v) == 0:
        return None
    out: List[List[float]] = []
    for row in v:
        if not isinstance(row, (list, tuple)) or len(row) != 3:
            return None
        if not all(_is_finite_number(n) for n in row):
            return None
        out.append([float(row[0]), float(row[1]), float(row[2])])
    return out


def _as_edge_list(v: Any) -> Optional[List[List[int]]]:
    if not isinstance(v, list):
        return None
    out: List[List[int]] = []
    for e in v:
        if not isinstance(e, (list, tuple)) or len(e) != 2:
            return None
        a, b = e
        if not isinstance(a, int) or not isinstance(b, int):
            return None
        out.append([int(a), int(b)])
    return out


def _read_jsonl(path: PathLike) -> Iterable[Tuple[int, Dict[str, Any]]]:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            s = line.strip()
            if not s:
                continue
            yield idx, json.loads(s)


def validate_blueprints_jsonl(
    blueprints_jsonl: PathLike,
    *,
    require_lods: bool = False,
    require_kind: bool = True,
    max_records: Optional[int] = None,
    strict: bool = False,
) -> SchemaValidationResult:
    """Validate a blueprint DB file.

    This is a validator, not a normalizer: it doesn't rewrite your DB.

    Accepted schema variants (to tolerate version drift):
    - vertices_m OR vertices
    - edges OR edges_idx
    - lod_edges OR lods

    Validation checks:
    - blueprint_id exists and is a string
    - vertices is Nx3 finite float
    - edges is Mx2 int, indices in bounds, no self-loops
    - lod_edges keys are strings, values are edge lists
    """

    res = SchemaValidationResult(path=str(blueprints_jsonl))

    try:
        for lineno, rec in _read_jsonl(blueprints_jsonl):
            if max_records is not None and res.total_records >= max_records:
                res.warnings.append(
                    f"Stopped after max_records={max_records} (file may have more records)."
                )
                break

            res.total_records += 1

            # --- id ---
            blueprint_id = rec.get("blueprint_id") or rec.get("id")
            if not isinstance(blueprint_id, str) or not blueprint_id.strip():
                res.errors.append(
                    f"{blueprints_jsonl}:{lineno}: missing/invalid blueprint_id (expected non-empty string)."
                )
                continue

            # --- kind ---
            kind = rec.get("kind") or rec.get("visual_kind")
            if require_kind and (not isinstance(kind, str) or not kind.strip()):
                res.warnings.append(
                    f"{blueprints_jsonl}:{lineno} ({blueprint_id}): missing kind; recommend setting kind for mapping + validation."
                )

            # --- vertices ---
            verts_raw = rec.get("vertices_m")
            if verts_raw is None:
                verts_raw = rec.get("vertices")
            verts = _as_vec3_list(verts_raw)
            if verts is None:
                res.errors.append(
                    f"{blueprints_jsonl}:{lineno} ({blueprint_id}): invalid vertices (expected list of [x,y,z] finite)."
                )
                continue
            n_verts = len(verts)
            if n_verts < 2:
                res.errors.append(
                    f"{blueprints_jsonl}:{lineno} ({blueprint_id}): too few vertices ({n_verts})."
                )
                continue

            # --- edges ---
            edges_raw = rec.get("edges")
            if edges_raw is None:
                edges_raw = rec.get("edges_idx")
            edges = _as_edge_list(edges_raw)
            if edges is None:
                res.errors.append(
                    f"{blueprints_jsonl}:{lineno} ({blueprint_id}): invalid edges (expected list of [i,j] ints)."
                )
                continue

            # index bounds
            bad = 0
            self_loops = 0
            for a, b in edges:
                if a == b:
                    self_loops += 1
                if not (0 <= a < n_verts) or not (0 <= b < n_verts):
                    bad += 1
            if bad:
                res.errors.append(
                    f"{blueprints_jsonl}:{lineno} ({blueprint_id}): {bad} edges out of vertex bounds (0..{n_verts-1})."
                )
                continue
            if self_loops:
                res.warnings.append(
                    f"{blueprints_jsonl}:{lineno} ({blueprint_id}): {self_loops} self-loop edges (i==j)."
                )

            # --- lod edges ---
            lods_raw = rec.get("lod_edges")
            if lods_raw is None:
                lods_raw = rec.get("lods")

            if lods_raw is None:
                if require_lods:
                    res.errors.append(
                        f"{blueprints_jsonl}:{lineno} ({blueprint_id}): missing lod_edges (required by require_lods=True)."
                    )
                    continue
            else:
                if not isinstance(lods_raw, dict):
                    res.errors.append(
                        f"{blueprints_jsonl}:{lineno} ({blueprint_id}): lod_edges must be a dict of lod_name -> edges list."
                    )
                    continue
                for lod_name, lod_edges_raw in lods_raw.items():
                    if not isinstance(lod_name, str):
                        res.errors.append(
                            f"{blueprints_jsonl}:{lineno} ({blueprint_id}): lod_edges key must be str, got {type(lod_name)}."
                        )
                        continue
                    lod_edges = _as_edge_list(lod_edges_raw)
                    if lod_edges is None:
                        res.errors.append(
                            f"{blueprints_jsonl}:{lineno} ({blueprint_id}): lod '{lod_name}' invalid edge list."
                        )
                        continue
                    # bounds check
                    bad2 = 0
                    for a, b in lod_edges:
                        if not (0 <= a < n_verts) or not (0 <= b < n_verts):
                            bad2 += 1
                    if bad2:
                        res.errors.append(
                            f"{blueprints_jsonl}:{lineno} ({blueprint_id}): lod '{lod_name}' has {bad2} edges out of bounds."
                        )

            # --- anchors optional ---
            anchors = rec.get("anchors")
            if anchors is not None:
                if not isinstance(anchors, dict):
                    res.errors.append(
                        f"{blueprints_jsonl}:{lineno} ({blueprint_id}): anchors must be dict[str, [x,y,z]]."
                    )
                    continue
                for name, vec in anchors.items():
                    if not isinstance(name, str) or not name:
                        res.errors.append(
                            f"{blueprints_jsonl}:{lineno} ({blueprint_id}): anchor name must be non-empty string."
                        )
                        continue
                    if not isinstance(vec, (list, tuple)) or len(vec) != 3 or not all(
                        _is_finite_number(n) for n in vec
                    ):
                        res.errors.append(
                            f"{blueprints_jsonl}:{lineno} ({blueprint_id}): anchor '{name}' invalid vec3."
                        )
                        continue

            res.valid_records += 1

    except FileNotFoundError:
        res.errors.append(f"Blueprint DB not found: {blueprints_jsonl}")
    except json.JSONDecodeError as e:
        res.errors.append(f"JSON parse error in {blueprints_jsonl}: {e}")
    except Exception as e:  # pragma: no cover
        res.errors.append(f"Unhandled error validating {blueprints_jsonl}: {type(e).__name__}: {e}")
    if strict and res.warnings:
        # Promote warnings to errors in strict mode.
        res.errors.extend([f"STRICT: {w}" for w in res.warnings])
        res.warnings.clear()

    return res

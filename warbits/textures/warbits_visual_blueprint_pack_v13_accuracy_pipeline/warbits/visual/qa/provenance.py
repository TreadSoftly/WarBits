from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

PathLike = Union[str, Path]


@dataclass(frozen=True)
class ProvenanceRecord:
    blueprint_id: str
    source: str
    license: str
    attribution: Optional[str] = None
    notes: Optional[str] = None


def load_provenance(path: PathLike) -> Dict[str, ProvenanceRecord]:
    """Load provenance from JSON or JSONL.

    JSON: either a list of records or a dict mapping blueprint_id -> record.
    JSONL: one record per line.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))

    text = p.read_text(encoding="utf-8", errors="replace")
    if p.suffix.lower() == ".jsonl":
        records: Dict[str, ProvenanceRecord] = {}
        for ln, raw in enumerate(text.splitlines(), start=1):
            s = raw.strip()
            if not s:
                continue
            obj = json.loads(s)
            rec = _coerce_record(obj, ln)
            records[rec.blueprint_id] = rec
        return records

    obj = json.loads(text)
    if isinstance(obj, dict):
        out: Dict[str, ProvenanceRecord] = {}
        for k, v in obj.items():
            if isinstance(v, dict) and "blueprint_id" not in v:
                v = dict(v)
                v["blueprint_id"] = str(k)
            rec = _coerce_record(v, None)
            out[rec.blueprint_id] = rec
        return out

    if isinstance(obj, list):
        out = {}
        for item in obj:
            rec = _coerce_record(item, None)
            out[rec.blueprint_id] = rec
        return out

    raise TypeError(f"Unsupported provenance json format: {type(obj)}")


def _coerce_record(obj: Any, ln: Optional[int]) -> ProvenanceRecord:
    if not isinstance(obj, dict):
        raise TypeError(f"Provenance record must be an object at line {ln}")
    bid = str(obj.get("blueprint_id") or obj.get("id") or "").strip()
    if not bid:
        raise ValueError(f"Provenance record missing blueprint_id at line {ln}")
    source = str(obj.get("source") or obj.get("origin") or "").strip()
    lic = str(obj.get("license") or obj.get("licence") or "").strip()
    if not source:
        source = "UNKNOWN"
    if not lic:
        lic = "UNKNOWN"
    return ProvenanceRecord(
        blueprint_id=bid,
        source=source,
        license=lic,
        attribution=(str(obj["attribution"]).strip() if obj.get("attribution") else None),
        notes=(str(obj["notes"]).strip() if obj.get("notes") else None),
    )


def _check_provenance_ids(
    blueprint_ids: Sequence[str],
    provenance: Dict[str, ProvenanceRecord],
    *,
    strict: bool,
    treat_prefixes_as_generated: Sequence[str] = ("proc:", "procedural:")
) -> Tuple[List[str], List[str]]:
    """Return (errors, warnings) for provenance coverage."""

    errors: List[str] = []
    warnings: List[str] = []

    for bid in blueprint_ids:
        is_generated = any(bid.startswith(p) for p in treat_prefixes_as_generated)
        if is_generated:
            continue
        if bid not in provenance:
            msg = f"Missing provenance for blueprint_id '{bid}'"
            if strict:
                errors.append(msg)
            else:
                warnings.append(msg)

    return errors, warnings


@dataclass
class ProvenanceReport:
    """Human-friendly report for provenance/attribution checks."""

    provenance_path: str
    strict: bool
    total_blueprints: int
    mesh_blueprints: int
    records_found: int
    missing_ids: List[str]
    errors: List[str]

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def check_provenance(
    blueprints_jsonl_path: PathLike,
    provenance_path: PathLike,
    strict: bool = False,
    procedural_prefixes: Sequence[str] = ("proc:",),
    allow_generated_flag: bool = True,
) -> ProvenanceReport:
    """Check that mesh-derived blueprints have provenance/license records.

    Rules:
    - A blueprint is considered *procedural* if:
      - blueprint_id starts with a prefix in procedural_prefixes, OR
      - record has generated=true (if allow_generated_flag)
    - Everything else is treated as mesh-derived and should have a provenance record.

    In strict mode: missing provenance is an error.
    In non-strict mode: missing provenance is still reported as errors (so CI can fail),
    but you may choose not to run strict in local workflows.
    """

    blueprints_jsonl_path = Path(blueprints_jsonl_path)
    provenance_path = Path(provenance_path)

    ids_all: List[str] = []
    ids_mesh: List[str] = []

    with blueprints_jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            bid = str(obj.get("blueprint_id") or obj.get("id") or "").strip()
            if not bid:
                continue
            ids_all.append(bid)
            is_proc = any(bid.startswith(p) for p in procedural_prefixes)
            if allow_generated_flag and bool(obj.get("generated") is True):
                is_proc = True
            if not is_proc:
                ids_mesh.append(bid)

    records = load_provenance_records(provenance_path)
    missing = sorted([bid for bid in ids_mesh if bid not in records])

    errors: List[str] = []
    if missing:
        msg = (
            f"Missing provenance records for {len(missing)} mesh blueprints. "
            f"Example(s): {missing[:10]}"
        )
        errors.append(msg)

    # strict doesn't change the current error list (we always treat missing as errors),
    # but we keep it in the report because it matters for packaging.
    return ProvenanceReport(
        provenance_path=str(provenance_path),
        strict=strict,
        total_blueprints=len(ids_all),
        mesh_blueprints=len(ids_mesh),
        records_found=len(records),
        missing_ids=missing,
        errors=errors,
    )

# Back-compat alias
load_provenance_records = load_provenance


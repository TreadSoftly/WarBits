"""Stable JSON serialization helpers.

Goals:
- Deterministic key ordering (sort_keys=True).
- Safe conversion of dataclasses, numpy arrays/scalars, and pathlib Paths.
- No hidden global state.

This is used for event logs, manifests, and reproducibility artifacts.
"""

from __future__ import annotations

import base64
import dataclasses
import json
from pathlib import Path
from typing import Any, Mapping, cast

try:
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover - numpy should exist in WarBits, but keep import-safe
    np = None  # type: ignore


def to_jsonable(obj: Any) -> Any:
    """Convert common WarBits objects into JSON-serializable forms."""
    if obj is None:
        return None

    # Dataclasses
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {k: to_jsonable(v) for k, v in dataclasses.asdict(obj).items()}

    # pathlib
    if isinstance(obj, Path):
        return str(obj)

    # bytes
    if isinstance(obj, (bytes, bytearray)):
        return {"__bytes_b64__": base64.b64encode(bytes(obj)).decode("ascii")}

    # numpy
    if np is not None:
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.floating,)):
            return float(obj.item())
        if isinstance(obj, (np.integer,)):
            return int(obj.item())
        if isinstance(obj, (np.bool_,)):
            return bool(obj)

    # Mappings / sequences
    if isinstance(obj, Mapping):
        obj_map = cast(Mapping[Any, Any], obj)
        return {str(k): to_jsonable(v) for k, v in obj_map.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in cast(list[Any], obj)]

    # Primitives
    if isinstance(obj, (str, int, float, bool)):
        return obj

    # Fallback: string representation (explicitly not ideal, but better than crashing)
    return {"__repr__": repr(obj)}


def json_dumps_stable(obj: Any, *, indent: int = 2) -> str:
    """Stable JSON dump (sorted keys) with WarBits conversions."""
    return json.dumps(
        to_jsonable(obj),
        indent=indent,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def json_dump_file(path: str | Path, obj: Any, *, indent: int = 2) -> None:
    """Write stable JSON to disk."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json_dumps_stable(obj, indent=indent), encoding="utf-8")

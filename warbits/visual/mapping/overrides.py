"""Load manual visual mapping overrides.

Overrides are the human-safe mechanism to force:
- a specific blueprint_id for an entity
- a style preset
- scale factor
- LOD policy tweaks

Format supports:
- JSON dict (recommended):
    {
      "vehicle": {"F-15C": {"blueprint_id": "mesh:f15c", "scale": 1.0}},
      "weapon":  {"AIM-9L": {"blueprint_id": "mesh:aim9l"}}
    }
- JSONL (one binding per line):
    {"entity_kind": "vehicle", "entity_id": "F-15C", "binding": {...}}

All keys are treated as opaque strings.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping, cast

from warbits.visual.mapping.types import VisualBinding, VisualMap


def load_overrides(path: str | Path) -> Dict[str, Dict[str, Any]]:
    """Return nested dict overrides[kind][entity_id] -> binding dict."""

    path = Path(path)
    if not path.exists():
        return {}

    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return {}

    # Heuristic: JSONL if it starts with '{' and contains multiple lines.
    if "\n" in text and text.lstrip().startswith("{"):
        out: Dict[str, Dict[str, Any]] = {}
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if not isinstance(row, Mapping):
                continue
            row_map = cast(Mapping[str, Any], row)
            kind = str(row_map.get("entity_kind", ""))
            entity_id = str(row_map.get("entity_id", ""))
            binding = row_map.get("binding")
            if not kind or not entity_id or not isinstance(binding, Mapping):
                continue
            out.setdefault(kind, {})[entity_id] = dict(cast(Mapping[str, Any], binding))
        return out

    # Otherwise treat as JSON dict.
    payload = json.loads(text)
    if not isinstance(payload, Mapping):
        raise ValueError(f"Overrides JSON must be a dict; got {type(payload)}")
    payload = cast(Mapping[str, Any], payload)

    out2: Dict[str, Dict[str, Any]] = {}
    for kind, by_id in payload.items():
        if not isinstance(by_id, Mapping):
            continue
        by_id_map = cast(Mapping[str, Any], by_id)
        out2[str(kind)] = {
            str(k): dict(cast(Mapping[str, Any], v))
            for k, v in by_id_map.items()
            if isinstance(v, Mapping)
        }
    return out2


def apply_overrides(vmap: VisualMap, overrides: Mapping[str, Any]) -> VisualMap:
    """Return a new VisualMap with overrides merged in."""

    merged = VisualMap(
        bindings=dict(vmap.bindings),
        defaults=dict(vmap.defaults),
        version=str(vmap.version),
    )

    for kind, by_id in overrides.items():
        if not isinstance(by_id, Mapping):
            continue
        kind = str(kind)
        by_id_map = cast(Mapping[str, Any], by_id)
        for entity_id, binding_dict in by_id_map.items():
            if not isinstance(binding_dict, Mapping):
                continue
            merged.set(
                kind,
                str(entity_id),
                VisualBinding.from_dict(dict(cast(Mapping[str, Any], binding_dict))),
            )

    return merged

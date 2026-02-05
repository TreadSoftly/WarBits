"""Build a VisualMap from WarBits data and an optional blueprint DB.

This is the bridge between:
- warbits/data/*.json (vehicle_id, weapon_id, ...)
- warbits/visual blueprints (mesh/procedural)

The output VisualMap is a small JSON/JSONL file that the renderer can load fast
at runtime.

We intentionally keep this module permissive about the DataStore interface, so
it can be used during ongoing refactors.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Iterable, Mapping, Optional, cast

if TYPE_CHECKING:  # pragma: no cover
    from warbits.visual.blueprint_db import BlueprintDB

from warbits.visual.mapping.rules import resolve_visual_binding
from warbits.visual.mapping.types import VisualMap


def _maybe_call(obj: Any, name: str, *args: Any, **kwargs: Any) -> Any:
    fn = getattr(obj, name, None)
    if callable(fn):
        return fn(*args, **kwargs)
    return None


def _get_store_dict(store: Any, attr: str) -> Optional[Dict[str, Any]]:
    v = getattr(store, attr, None)
    return cast(Dict[str, Any], v) if isinstance(v, dict) else None


def iter_entity_ids(store: Any) -> Dict[str, list[str]]:
    """Return {'vehicle': [...], 'weapon': [...], 'warhead': [...], 'sensor': [...]}

    Best-effort: returns empty list for missing categories.
    """

    out: Dict[str, list[str]] = {}
    for kind in ("vehicle", "weapon", "warhead", "sensor"):
        ids: Optional[Iterable[str]] = None

        # Prefer explicit iterator methods if present.
        ids = _maybe_call(store, f"all_{kind}_ids")
        if ids is None:
            ids = _maybe_call(store, f"iter_{kind}_ids")

        # Fall back to dict attribute collections.
        if ids is None:
            d = _get_store_dict(store, f"{kind}s")
            if d is not None:
                ids = d.keys()

        out[kind] = sorted(list(ids)) if ids is not None else []

    return out


def _get_spec(store: Any, kind: str, entity_id: str) -> Mapping[str, Any]:
    # Prefer accessor methods.
    spec = _maybe_call(store, f"get_{kind}", entity_id)
    if spec is not None:
        return cast(Mapping[str, Any], spec) if isinstance(spec, Mapping) else asdict(spec)

    # Fall back to dict attributes.
    d = _get_store_dict(store, f"{kind}s")
    if d is not None and entity_id in d:
        v = d[entity_id]
        return cast(Mapping[str, Any], v) if isinstance(v, Mapping) else asdict(v)

    return {"id": entity_id}


def build_visual_map(
    *,
    store: Any,
    blueprints: Optional[BlueprintDB] = None,
    overrides: Optional[Mapping[str, Any]] = None,
    default_style: str = "holo_green",
) -> VisualMap:
    vmap = VisualMap()
    ids_by_kind = iter_entity_ids(store)

    for kind, ids in ids_by_kind.items():
        for entity_id in ids:
            spec = _get_spec(store, kind, entity_id)
            binding = resolve_visual_binding(
                entity_kind=kind,
                entity_id=entity_id,
                spec=spec,
                blueprints=blueprints,
                overrides=overrides,
                default_style=default_style,
            )

            vmap.set(kind, entity_id, binding)

    return vmap


def write_visual_map_json(path: str | Path, vmap: VisualMap) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = vmap.to_dict()
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_visual_map_jsonl(path: str | Path, vmap: VisualMap) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    for (kind, entity_id), binding in sorted(vmap.bindings.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        lines.append(
            json.dumps(
                {
                    "entity_kind": kind,
                    "entity_id": entity_id,
                    "binding": binding.to_dict(),
                },
                sort_keys=True,
            )
        )

    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

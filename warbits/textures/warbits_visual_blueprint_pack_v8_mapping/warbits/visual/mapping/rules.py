"""Rule-based selection of visual blueprints.

The mapping problem:
- WarBits knows about *entities* by canonical IDs (vehicle_id, weapon_id, ...).
- The renderer wants a *Blueprint* (a wireframe graph).

We support two blueprint sources:
1) Mesh-derived blueprints: ingested from .obj/.glb/etc into a blueprint DB.
2) Procedural blueprints: generated from specs when no mesh blueprint exists.

Human override always wins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Mapping, Optional, cast

if TYPE_CHECKING:  # pragma: no cover
    from warbits.visual.blueprint_db import BlueprintDB

from warbits.visual.mapping.derive import derive_procedural_binding
from warbits.visual.mapping.types import VisualBinding


def _candidate_blueprint_ids(entity_kind: str, entity_id: str) -> list[str]:
    # Keep these deterministic (stable order).
    return [
        f"{entity_kind}:{entity_id}",
        f"{entity_kind}:{entity_id.lower()}",
        f"{entity_kind}:{entity_id.replace(' ', '_')}",
    ]


def resolve_visual_binding(
    *,
    entity_kind: str,
    entity_id: str,
    spec: Mapping[str, Any],
    blueprints: Optional[BlueprintDB] = None,
    overrides: Optional[Mapping[str, Any]] = None,
    default_style: str = "holo_green",
) -> VisualBinding:
    """Resolve one entity -> VisualBinding.

    `overrides` is typically loaded from a JSON file. Two supported formats:

    Format A (simple):
      {"vehicle:F-16C": {"blueprint_id": "mesh:f16c", "scale": 1.0}}

    Format B (kind/id nested):
      {"vehicle": {"F-16C": {"blueprint_id": "mesh:f16c"}}}

    If a field is missing, we fall back.
    """

    # 1) Human override.
    override_key = f"{entity_kind}:{entity_id}"
    if overrides:
        ov = None
        if override_key in overrides:
            ov = overrides[override_key]
        else:
            ov_kind = overrides.get(entity_kind)
            if isinstance(ov_kind, dict):
                ov_kind_map = cast(Mapping[str, Any], ov_kind)
                if entity_id in ov_kind_map:
                    ov = ov_kind_map[entity_id]

        if isinstance(ov, dict):
            ov_map = cast(Mapping[str, Any], ov)
            b = VisualBinding(
                blueprint_id=str(ov_map.get("blueprint_id") or ov_map.get("blueprint") or ""),
                source=str(ov_map.get("source") or "override"),
                params=dict(ov_map.get("params") or {}),
                scale=float(ov_map.get("scale") or 1.0),
                style=str(ov_map.get("style") or default_style),
                lod=dict(ov_map.get("lod") or {}),
                meta={"override": True},
            )
            if b.blueprint_id:
                return b

    # 2) Mesh blueprint exists?
    if blueprints is not None:
        for cand in _candidate_blueprint_ids(entity_kind, entity_id):
            if blueprints.get(cand) is not None:
                return VisualBinding(
                    blueprint_id=cand,
                    source="mesh",
                    params={},
                    scale=1.0,
                    style=default_style,
                    lod={},
                    meta={},
                )

    # 3) Procedural fallback.
    template_key, params = derive_procedural_binding(spec)
    return VisualBinding(
        blueprint_id=template_key,
        source="procedural",
        params=params,
        scale=1.0,
        style=default_style,
        lod={},
        meta={},
    )

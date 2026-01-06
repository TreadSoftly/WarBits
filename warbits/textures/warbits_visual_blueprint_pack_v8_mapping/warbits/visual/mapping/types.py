"""Visual mapping types.

This layer sits between:
  - WarBits *simulation/data IDs* (vehicle_id, weapon_id, etc)
  - Visual blueprints (mesh-derived or procedural)

The goal is to make "pick any vehicle" work without hardcoding per-entity
renderer logic.

Design constraints:
- Deterministic: same inputs -> same outputs (stable JSON ordering).
- Renderer-agnostic: mapping has no Matplotlib/Panda3D imports.
- Portable: JSON/JSONL; no binary formats.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional, Tuple


@dataclass(frozen=True)
class VisualBinding:
    """Resolved visual binding for one entity id.

    blueprint_id:
        The blueprint record to render.

        Conventions:
        - If blueprint_id starts with "proc:", it's a procedural template id.
          Example: "proc:aircraft" or "proc:ordnance:mssl".
        - Otherwise it's assumed to be a concrete blueprint in a BlueprintDB.

    params:
        Template params for procedural generation OR runtime rendering hints.
        (Must be JSON-serializable.)

    scale:
        Uniform scale multiplier applied after blueprint vertices are generated.

    style:
        Style preset key. Renderers interpret this via their own style tables.

    lod:
        Optional LOD overrides. Common keys:
            - "tier": 0/1/2/3
            - "max_edges": int
            - "near_m": float
            - "far_m": float

    meta:
        Provenance / debugging hints.
    """

    blueprint_id: str
    params: Dict[str, Any] = field(default_factory=dict)
    scale: float = 1.0
    style: str = "holo_green"
    lod: Dict[str, Any] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        # Stable key order for deterministic JSON.
        return {
            "blueprint_id": self.blueprint_id,
            "params": dict(self.params),
            "scale": float(self.scale),
            "style": str(self.style),
            "lod": dict(self.lod),
            "meta": dict(self.meta),
        }

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> "VisualBinding":
        return VisualBinding(
            blueprint_id=str(d.get("blueprint_id", "")),
            params=dict(d.get("params", {})),
            scale=float(d.get("scale", 1.0)),
            style=str(d.get("style", "holo_green")),
            lod=dict(d.get("lod", {})),
            meta=dict(d.get("meta", {})),
        )


@dataclass
class VisualMap:
    """Mapping from (kind, id) -> VisualBinding.

    kind examples:
      - "vehicle"
      - "weapon"
      - "warhead"
      - "sensor"
      - "effect" (optional)
    """

    bindings: Dict[Tuple[str, str], VisualBinding] = field(default_factory=dict)
    defaults: Dict[str, VisualBinding] = field(default_factory=dict)
    version: str = "1"

    def set(self, kind: str, entity_id: str, binding: VisualBinding) -> None:
        self.bindings[(str(kind), str(entity_id))] = binding

    def get(self, kind: str, entity_id: str) -> Optional[VisualBinding]:
        return self.bindings.get((str(kind), str(entity_id)))

    def get_or_default(self, kind: str, entity_id: str) -> VisualBinding:
        b = self.get(kind, entity_id)
        if b is not None:
            return b
        d = self.defaults.get(kind)
        if d is not None:
            return d
        # Last resort.
        return VisualBinding(blueprint_id="proc:unknown")

    def items(self) -> Iterable[Tuple[Tuple[str, str], VisualBinding]]:
        return self.bindings.items()

    def to_dict(self) -> Dict[str, Any]:
        # Emit as list to keep deterministic ordering and allow duplicate checks.
        items: List[Dict[str, Any]] = []
        for (kind, eid), bind in sorted(self.bindings.items(), key=lambda kv: (kv[0][0], kv[0][1])):
            items.append({
                "kind": kind,
                "id": eid,
                "binding": bind.to_dict(),
            })

        defaults: Dict[str, Any] = {}
        for kind in sorted(self.defaults.keys()):
            defaults[kind] = self.defaults[kind].to_dict()

        return {
            "version": str(self.version),
            "defaults": defaults,
            "items": items,
        }

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> "VisualMap":
        vm = VisualMap(version=str(d.get("version", "1")))
        defaults = d.get("defaults", {}) or {}
        for kind, bd in dict(defaults).items():
            vm.defaults[str(kind)] = VisualBinding.from_dict(bd)

        for it in d.get("items", []) or []:
            kind = str(it.get("kind", ""))
            eid = str(it.get("id", ""))
            bind = VisualBinding.from_dict(it.get("binding", {}))
            if kind and eid:
                vm.set(kind, eid, bind)
        return vm

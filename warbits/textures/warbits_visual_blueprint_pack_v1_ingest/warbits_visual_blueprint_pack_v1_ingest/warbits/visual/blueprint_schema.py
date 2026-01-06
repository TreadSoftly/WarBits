from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Tuple

BlueprintKind = Literal[
    "vehicle",
    "weapon",
    "sensor",
    "effect",
    "terrain_prop",
]


def _as_list3(v: Any) -> List[float]:
    if isinstance(v, (list, tuple)) and len(v) == 3:
        return [float(v[0]), float(v[1]), float(v[2])]
    raise TypeError(f"Expected 3-vector, got: {v!r}")


@dataclass(frozen=True)
class BlueprintRecord:
    """A renderer-agnostic wireframe blueprint.

    Coordinates:
    - meters
    - canonical axes: X forward, Y left, Z up (project convention)
    """

    blueprint_id: str
    kind: BlueprintKind
    vertices_m: List[List[float]]
    edges: List[Tuple[int, int]]

    tags: List[str] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "blueprint_id": self.blueprint_id,
            "kind": self.kind,
            "vertices_m": [list(map(float, v)) for v in self.vertices_m],
            "edges": [[int(a), int(b)] for (a, b) in self.edges],
            "tags": list(self.tags),
            "meta": dict(self.meta),
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "BlueprintRecord":
        bp_id = str(d["blueprint_id"])
        kind = d["kind"]
        vertices = [_as_list3(v) for v in d.get("vertices_m", [])]
        edges_raw = d.get("edges", [])
        edges: List[Tuple[int, int]] = []
        for e in edges_raw:
            if not isinstance(e, (list, tuple)) or len(e) != 2:
                raise TypeError(f"Bad edge: {e!r}")
            edges.append((int(e[0]), int(e[1])))
        tags = [str(x) for x in d.get("tags", [])]
        meta = d.get("meta", {})
        if not isinstance(meta, dict):
            raise TypeError("meta must be dict")
        return BlueprintRecord(
            blueprint_id=bp_id,
            kind=kind,
            vertices_m=vertices,
            edges=edges,
            tags=tags,
            meta=meta,
        )

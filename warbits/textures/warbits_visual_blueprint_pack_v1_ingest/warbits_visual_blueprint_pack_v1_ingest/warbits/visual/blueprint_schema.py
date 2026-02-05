from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Tuple, cast

BlueprintKind = Literal[
    "vehicle",
    "weapon",
    "sensor",
    "effect",
    "terrain_prop",
]


def _empty_str_list() -> list[str]:
    return []


def _empty_meta_dict() -> dict[str, Any]:
    return {}


def _as_list3(v: Any) -> list[float]:
    if isinstance(v, (list, tuple)):
        seq = cast(list[object] | tuple[object, ...], v)
        if len(seq) == 3 and all(isinstance(x, (int, float)) for x in seq):
            x0 = cast(float, seq[0])
            x1 = cast(float, seq[1])
            x2 = cast(float, seq[2])
            return [float(x0), float(x1), float(x2)]
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
    vertices_m: list[list[float]]
    edges: list[Tuple[int, int]]

    tags: list[str] = field(default_factory=_empty_str_list)
    meta: dict[str, Any] = field(default_factory=_empty_meta_dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "blueprint_id": self.blueprint_id,
            "kind": self.kind,
            "vertices_m": [list(map(float, v)) for v in self.vertices_m],
            "edges": [[int(a), int(b)] for (a, b) in self.edges],
            "tags": list(self.tags),
            "meta": dict(self.meta),
        }

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "BlueprintRecord":
        bp_id = str(d["blueprint_id"])
        kind = d["kind"]
        vertices = [_as_list3(v) for v in d.get("vertices_m", [])]
        edges_raw = d.get("edges", [])
        edges: list[Tuple[int, int]] = []
        for e in edges_raw:
            if not isinstance(e, (list, tuple)):
                raise TypeError(f"Bad edge: {e!r}")
            seq = cast(list[object] | tuple[object, ...], e)
            if len(seq) != 2:
                raise TypeError(f"Bad edge: {e!r}")
            if not isinstance(seq[0], (int, float)) or not isinstance(seq[1], (int, float)):
                raise TypeError(f"Bad edge: {e!r}")
            edges.append((int(seq[0]), int(seq[1])))
        tags = [str(x) for x in d.get("tags", [])]
        meta = d.get("meta", {})
        if not isinstance(meta, dict):
            raise TypeError("meta must be dict")
        meta = cast(dict[str, Any], meta)
        return BlueprintRecord(
            blueprint_id=bp_id,
            kind=kind,
            vertices_m=vertices,
            edges=edges,
            tags=tags,
            meta=meta,
        )

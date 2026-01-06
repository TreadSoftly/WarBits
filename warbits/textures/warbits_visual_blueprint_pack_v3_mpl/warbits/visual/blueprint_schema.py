from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Mapping, Optional, Sequence, Tuple


Vec3 = Tuple[float, float, float]
Vec2 = Tuple[float, float]
Edge = Tuple[int, int]

BlueprintKind = Literal["vehicle", "weapon", "sensor", "effect"]


@dataclass(frozen=True)
class Outline2D:
    """2D line drawing blueprint (typically imported from SVG).

    Notes:
    - points are in an arbitrary 2D coordinate system (usually SVG pixels or a normalized unit square).
    - renderers decide how to place this in 3D (billboard, extrusion, etc.).
    """
    points: Tuple[Vec2, ...]
    edges: Tuple[Edge, ...]
    view: str = "unknown"  # e.g., "side", "top", "front"
    units: str = "px"      # "px" | "norm" | other
    meta: Mapping[str, Any] = field(default_factory=dict)

    def to_json_obj(self) -> Dict[str, Any]:
        return {
            "points": [list(p) for p in self.points],
            "edges": [list(e) for e in self.edges],
            "view": self.view,
            "units": self.units,
            "meta": dict(self.meta),
        }

    def to_dict(self) -> Dict[str, Any]:
        # Back-compat alias
        return self.to_json_obj()

    @staticmethod
    def from_json_obj(obj: Mapping[str, Any]) -> "Outline2D":
        points = tuple((float(p[0]), float(p[1])) for p in obj.get("points", []))
        edges = tuple((int(e[0]), int(e[1])) for e in obj.get("edges", []))
        return Outline2D(
            points=points,
            edges=edges,
            view=str(obj.get("view", "unknown")),
            units=str(obj.get("units", "px")),
            meta=dict(obj.get("meta", {})),
        )

    @staticmethod
    def from_dict(obj: Mapping[str, Any]) -> "Outline2D":
        # Back-compat alias
        return Outline2D.from_json_obj(obj)


@dataclass(frozen=True)
class Blueprint:
    """Visual Blueprint record.

    A Blueprint is *renderer-agnostic*: it describes geometry as vertices + edges.

    - repr == "wire3d": use vertices_m + (edges and/or lod_edges).
    - repr == "outline2d": use outline2d.

    LOD convention:
    - "lod0" is the highest detail.
    - increasing lod index reduces edge count.
    """

    blueprint_id: str
    kind: str  # e.g., "vehicle", "weapon", "sensor", "effect"
    repr: str = "wire3d"  # "wire3d" | "outline2d" | future types

    # Wire3D representation
    vertices_m: Sequence[Vec3] = ()
    edges: Sequence[Edge] = ()
    lod_edges: Mapping[str, Sequence[Edge]] = field(default_factory=dict)

    # Outline2D representation
    outline2d: Optional[Outline2D] = None

    tags: Sequence[str] = ()
    meta: Mapping[str, Any] = field(default_factory=dict)

    # ---------------------------------------------------------------------
    # Validation / helpers
    # ---------------------------------------------------------------------
    def validate(self) -> None:
        if not self.blueprint_id:
            raise ValueError("blueprint_id is required")

        if self.repr == "wire3d":
            n = len(self.vertices_m)
            if n == 0:
                raise ValueError(f"{self.blueprint_id}: wire3d repr requires vertices_m")
            # Validate base edges
            _validate_edges(self.blueprint_id, self.edges, n, label="edges")
            # Validate LOD edges
            for lod_name, e in self.lod_edges.items():
                _validate_edges(self.blueprint_id, e, n, label=f"lod_edges[{lod_name}]")

        elif self.repr == "outline2d":
            if self.outline2d is None:
                raise ValueError(f"{self.blueprint_id}: outline2d repr requires outline2d data")
        else:
            raise ValueError(f"{self.blueprint_id}: unknown repr={self.repr!r}")

    def available_lods(self) -> Tuple[str, ...]:
        if not self.lod_edges:
            return ()
        # stable ordering: lod0, lod1, lod2..., then anything else alphabetically
        def _key(name: str) -> Tuple[int, str]:
            if name.startswith("lod") and name[3:].isdigit():
                return (0, f"{int(name[3:]):06d}")
            return (1, name)
        return tuple(sorted(self.lod_edges.keys(), key=_key))

    def select_edges(self, lod: Optional[str] = None) -> Tuple[Edge, ...]:
        """Return edges for requested LOD, or base edges if LOD not present."""
        if self.repr != "wire3d":
            return ()
        if lod and lod in self.lod_edges:
            return tuple((int(a), int(b)) for (a, b) in self.lod_edges[lod])
        return tuple((int(a), int(b)) for (a, b) in self.edges)

    # ---------------------------------------------------------------------
    # JSON (stable)
    # ---------------------------------------------------------------------
    def to_json_obj(self) -> Dict[str, Any]:
        obj: Dict[str, Any] = {
            "id": self.blueprint_id,
            "kind": self.kind,
            "repr": self.repr,
            "tags": list(self.tags) if self.tags else [],
            "meta": dict(self.meta),
        }
        if self.repr == "wire3d":
            obj["vertices_m"] = [list(v) for v in self.vertices_m]
            obj["edges"] = [list(e) for e in self.edges]
            if self.lod_edges:
                obj["lod_edges"] = {k: [list(e) for e in v] for k, v in self.lod_edges.items()}
        elif self.repr == "outline2d":
            obj["outline2d"] = self.outline2d.to_json_obj() if self.outline2d else None
        return obj

    def to_dict(self) -> Dict[str, Any]:
        # Back-compat alias (v1 used to_dict/from_dict)
        return self.to_json_obj()

    @staticmethod
    def from_json_obj(obj: Mapping[str, Any]) -> "Blueprint":
        blueprint_id = str(obj.get("id", ""))
        kind = str(obj.get("kind", "unknown"))
        repr_ = str(obj.get("repr", "wire3d"))
        tags = tuple(str(t) for t in obj.get("tags", []) or [])
        meta = dict(obj.get("meta", {}) or {})

        if repr_ == "wire3d":
            vertices_m = tuple((float(v[0]), float(v[1]), float(v[2])) for v in obj.get("vertices_m", []) or [])
            edges = tuple((int(e[0]), int(e[1])) for e in obj.get("edges", []) or [])
            lod_obj = obj.get("lod_edges", {}) or {}
            lod_edges = {str(k): tuple((int(e[0]), int(e[1])) for e in v) for k, v in lod_obj.items()}
            bp = Blueprint(
                blueprint_id=blueprint_id,
                kind=kind,
                repr=repr_,
                vertices_m=vertices_m,
                edges=edges,
                lod_edges=lod_edges,
                tags=tags,
                meta=meta,
            )
            return bp

        if repr_ == "outline2d":
            outline_obj = obj.get("outline2d", None)
            outline = Outline2D.from_json_obj(outline_obj) if isinstance(outline_obj, Mapping) else None
            bp = Blueprint(
                blueprint_id=blueprint_id,
                kind=kind,
                repr=repr_,
                outline2d=outline,
                tags=tags,
                meta=meta,
            )
            return bp

        # Unknown repr: keep record but mark as invalid until supported
        return Blueprint(
            blueprint_id=blueprint_id,
            kind=kind,
            repr=repr_,
            tags=tags,
            meta=meta,
        )

    @staticmethod
    def from_dict(obj: Mapping[str, Any]) -> "Blueprint":
        # Back-compat alias
        return Blueprint.from_json_obj(obj)


# Back-compat alias: older packs used BlueprintRecord
BlueprintRecord = Blueprint


def _validate_edges(blueprint_id: str, edges: Sequence[Edge], n_vertices: int, label: str) -> None:
    for i, e in enumerate(edges):
        if len(e) != 2:
            raise ValueError(f"{blueprint_id}: {label}[{i}] is not an edge pair: {e!r}")
        a, b = int(e[0]), int(e[1])
        if a < 0 or a >= n_vertices or b < 0 or b >= n_vertices:
            raise ValueError(
                f"{blueprint_id}: {label}[{i}] out of range (n={n_vertices}): ({a},{b})"
            )
        if a == b:
            raise ValueError(f"{blueprint_id}: {label}[{i}] is a self-edge: ({a},{b})")

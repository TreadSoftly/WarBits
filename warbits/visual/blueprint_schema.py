from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Literal, Mapping, Optional, Sequence, Tuple


Vec3 = Tuple[float, float, float]
Vec2 = Tuple[float, float]
Edge = Tuple[int, int]
AnchorMap = Mapping[str, Vec3]

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
    anchors: AnchorMap = field(default_factory=dict)
    source: Optional[str] = None
    units: str = "m"

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
            # Validate anchors if present.
            for name, vec in (self.anchors or {}).items():
                if not name:
                    raise ValueError(f"{self.blueprint_id}: anchor name must be a non-empty string")
                if len(vec) != 3:
                    raise ValueError(f"{self.blueprint_id}: anchor '{name}' must be a 3-vector")
                try:
                    float(vec[0])
                    float(vec[1])
                    float(vec[2])
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        f"{self.blueprint_id}: anchor '{name}' must contain numeric values"
                    ) from exc

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

    @property
    def edges_by_lod(self) -> Mapping[str, Sequence[Edge]]:
        """Compatibility: return {"base": edges, **lod_edges}."""
        combined: Dict[str, Sequence[Edge]] = {}
        if self.edges:
            combined["base"] = self.edges
        for name, edges in (self.lod_edges or {}).items():
            combined[name] = edges
        return combined

    @property
    def vertices(self) -> Sequence[Vec3]:
        """Compatibility alias for vertices_m."""
        return self.vertices_m

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
            if self.anchors:
                obj["anchors"] = {k: list(v) for k, v in self.anchors.items()}
            if self.source:
                obj["source"] = self.source
            if self.units:
                obj["units"] = self.units
        elif self.repr == "outline2d":
            obj["outline2d"] = self.outline2d.to_json_obj() if self.outline2d else None
        return obj

    def to_dict(self) -> Dict[str, Any]:
        # Back-compat alias (v1 used to_dict/from_dict)
        return self.to_json_obj()

    def to_json(self) -> Dict[str, Any]:
        # Back-compat alias used in older tooling.
        return self.to_json_obj()

    @staticmethod
    def from_json_obj(obj: Mapping[str, Any]) -> "Blueprint":
        blueprint_id = str(obj.get("id", ""))
        kind = str(obj.get("kind", "unknown"))
        repr_ = str(obj.get("repr", "wire3d"))
        tags = _coerce_tags(obj.get("tags"))
        meta = _coerce_meta(obj.get("meta"))

        if repr_ == "wire3d":
            verts_raw = obj.get("vertices_m")
            if verts_raw is None:
                verts_raw = obj.get("vertices")
            vertices_m = _coerce_vec3_list(verts_raw)

            edges_raw = obj.get("edges")
            if edges_raw is None:
                edges_raw = obj.get("edges_idx")
            edges = _coerce_edge_list(edges_raw)

            lod_obj = obj.get("lod_edges")
            if lod_obj is None:
                lod_obj = obj.get("lods")
            if lod_obj is None:
                lod_obj = obj.get("edges_by_lod")
            lod_edges, edges = _coerce_lod_edges(lod_obj, edges)

            anchors = _coerce_anchor_map(obj.get("anchors"))

            source = obj.get("source")
            source = str(source) if source is not None else None
            units = str(obj.get("units", "m"))
            bp = Blueprint(
                blueprint_id=blueprint_id,
                kind=kind,
                repr=repr_,
                vertices_m=vertices_m,
                edges=edges,
                lod_edges=lod_edges,
                anchors=anchors,
                source=source,
                units=units,
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


def _coerce_tags(raw: object) -> Tuple[str, ...]:
    if isinstance(raw, (list, tuple)):
        return tuple(str(item) for item in raw)
    return ()


def _coerce_meta(raw: object) -> Dict[str, Any]:
    if isinstance(raw, Mapping):
        return dict(raw)
    return {}


def _coerce_vec3_list(raw: object) -> Tuple[Vec3, ...]:
    if not isinstance(raw, list):
        return ()
    out: list[Vec3] = []
    for row in raw:
        if not isinstance(row, (list, tuple)) or len(row) != 3:
            continue
        try:
            out.append((float(row[0]), float(row[1]), float(row[2])))
        except (TypeError, ValueError):
            continue
    return tuple(out)


def _coerce_edge_list(raw: object) -> Tuple[Edge, ...]:
    if not isinstance(raw, list):
        return ()
    out: list[Edge] = []
    for row in raw:
        if not isinstance(row, (list, tuple)) or len(row) != 2:
            continue
        try:
            out.append((int(row[0]), int(row[1])))
        except (TypeError, ValueError):
            continue
    return tuple(out)


def _coerce_lod_edges(
    raw: object,
    base_edges: Tuple[Edge, ...],
) -> Tuple[Dict[str, Tuple[Edge, ...]], Tuple[Edge, ...]]:
    if not isinstance(raw, Mapping):
        return {}, base_edges
    lod_edges: Dict[str, Tuple[Edge, ...]] = {}
    edges = base_edges
    for key, value in raw.items():
        name = str(key)
        if name == "base":
            if not edges:
                edges = _coerce_edge_list(value)
            continue
        lod_edges[name] = _coerce_edge_list(value)
    return lod_edges, edges


def _coerce_anchor_map(raw: object) -> Dict[str, Vec3]:
    if not isinstance(raw, Mapping):
        return {}
    anchors: Dict[str, Vec3] = {}
    for key, value in raw.items():
        name = str(key)
        if isinstance(value, (list, tuple)) and len(value) == 3:
            try:
                anchors[name] = (float(value[0]), float(value[1]), float(value[2]))
            except (TypeError, ValueError):
                continue
    return anchors

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Literal, Optional, cast

EntityKind = Literal["aircraft", "ground", "weapon", "effect"]
SourceKind = Literal["procedural", "mesh", "silhouette_hull"]


def _empty_metadata() -> dict[str, Any]:
    return {}


def _dict_any(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return cast(dict[str, Any], value)
    return {}


def _as_vec3(values: Iterable[float]) -> tuple[float, float, float]:
    coords = list(values)
    return (float(coords[0]), float(coords[1]), float(coords[2]))


@dataclass(frozen=True)
class BlueprintSource:
    """Provenance and licensing metadata for a visual asset."""

    kind: SourceKind
    # Human-friendly source name (e.g., "FlightGear", "BlendSwap", "Wikimedia").
    name: str
    # URL(s) or file paths to the raw source.
    refs: tuple[str, ...] = ()
    # License identifier string (e.g., "CC0-1.0", "CC-BY-4.0", "GPL-2.0-or-later").
    license_id: str = "UNKNOWN"
    # Optional attribution text required by license.
    attribution: str = ""

    def to_json(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "name": self.name,
            "refs": list(self.refs),
            "license_id": self.license_id,
            "attribution": self.attribution,
        }

    @staticmethod
    def from_json(d: dict[str, Any]) -> "BlueprintSource":
        return BlueprintSource(
            kind=d["kind"],
            name=d.get("name", ""),
            refs=tuple(d.get("refs", [])),
            license_id=d.get("license_id", "UNKNOWN"),
            attribution=d.get("attribution", ""),
        )


@dataclass
class WireframeMesh:
    """A renderer-agnostic wireframe: vertices + edges in local space.

    Coordinate convention:
    - +X forward
    - +Y left
    - +Z up

    Units: meters
    """

    vertices_m: list[tuple[float, float, float]]
    edges: list[tuple[int, int]]
    # Optional group labels for style (e.g., silhouette vs ribs).
    edge_groups: Optional[list[str]] = None

    def validate(self) -> None:
        if not self.vertices_m:
            raise ValueError("WireframeMesh has no vertices.")
        n = len(self.vertices_m)
        for a, b in self.edges:
            if not (0 <= a < n and 0 <= b < n):
                raise ValueError(f"Edge ({a},{b}) out of bounds for n={n}.")
            if a == b:
                raise ValueError("WireframeMesh has self-edge.")
        if self.edge_groups is not None and len(self.edge_groups) != len(self.edges):
            raise ValueError("edge_groups length must match edges length.")

    def to_json(self) -> dict[str, Any]:
        return {
            "vertices_m": [list(v) for v in self.vertices_m],
            "edges": [list(e) for e in self.edges],
            "edge_groups": self.edge_groups,
        }

    @staticmethod
    def from_json(d: dict[str, Any]) -> "WireframeMesh":
        return WireframeMesh(
            vertices_m=[_as_vec3(v) for v in d["vertices_m"]],
            edges=[(int(e[0]), int(e[1])) for e in d["edges"]],
            edge_groups=d.get("edge_groups"),
        )


@dataclass
class VisualBlueprint:
    """A blueprint record for rendering an entity in WarBits style."""

    entity_id: str
    kind: EntityKind
    source: BlueprintSource

    # Option A: compiled mesh reference (preferred at runtime)
    compiled_ref: Optional[str] = None  # e.g. "assets/visual/compiled/f35a_lod0.npz"

    # Option B: embedded wireframe (useful for tests, placeholders)
    wireframe: Optional[WireframeMesh] = None

    # Option C: procedural params (archetype)
    procedural: dict[str, Any] = field(default_factory=_empty_metadata)

    # Metadata for search/filtering (nation, era, role, etc.)
    tags: dict[str, Any] = field(default_factory=_empty_metadata)

    def validate(self) -> None:
        if not self.entity_id:
            raise ValueError("VisualBlueprint.entity_id is required.")
        if self.compiled_ref is None and self.wireframe is None and not self.procedural:
            raise ValueError("VisualBlueprint must have compiled_ref, wireframe, or procedural params.")
        if self.wireframe is not None:
            self.wireframe.validate()

    def to_json(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "kind": self.kind,
            "source": self.source.to_json(),
            "compiled_ref": self.compiled_ref,
            "wireframe": None if self.wireframe is None else self.wireframe.to_json(),
            "procedural": self.procedural,
            "tags": self.tags,
        }

    @staticmethod
    def from_json(d: dict[str, Any]) -> "VisualBlueprint":
        wf = d.get("wireframe")
        return VisualBlueprint(
            entity_id=d["entity_id"],
            kind=d["kind"],
            source=BlueprintSource.from_json(d["source"]),
            compiled_ref=d.get("compiled_ref"),
            wireframe=None if wf is None else WireframeMesh.from_json(wf),
            procedural=_dict_any(d.get("procedural")),
            tags=_dict_any(d.get("tags")),
        )

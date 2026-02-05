"""WarBits visual blueprint system.

This package is intentionally engine/renderer-agnostic:
- Defines a compact wireframe "Blueprint" representation (nodes + edges).
- Utilities to ingest meshes into blueprints.
- LOD and transforms.
- Mapping from WarBits data IDs to blueprints.

Renderers (matplotlib, Panda3D, etc.) consume these primitives.

NOTE: This repository is built iteratively via "packs". To avoid import-hair
when only parts of the visual system is present, most imports are guarded.
"""

from __future__ import annotations

# Core schema / DB
try:
    from warbits.visual.blueprint_db import BlueprintDB, read_blueprints_jsonl, write_blueprints_jsonl
    from warbits.visual.blueprint_schema import Blueprint, BlueprintKind, BlueprintRecord, Edge, Outline2D, Vec2, Vec3
    from warbits.visual.lod import CameraModel, LODLevel, LODPolicy, projected_radius_px
    from warbits.visual.mesh_io import load_any_mesh
    from warbits.visual.registry import VisualRegistry
    from warbits.visual.transform import build_segments, transform_vertices
    from warbits.visual.wireframe_extract import extract_wireframe_edges
except Exception:  # pragma: no cover
    # Partial installs are allowed while iterating.
    pass

# Mapping layer
try:
    from warbits.visual.mapping import VisualBinding, VisualMap, build_visual_map, resolve_visual_binding
except Exception:  # pragma: no cover
    pass

__all__ = [
    # schema/db
    "Blueprint",
    "Edge",
    "Vec2",
    "Vec3",
    "Outline2D",
    "BlueprintKind",
    "BlueprintRecord",
    "BlueprintDB",
    "read_blueprints_jsonl",
    "write_blueprints_jsonl",
    "VisualRegistry",
    "build_segments",
    "transform_vertices",
    "LODLevel",
    "CameraModel",
    "projected_radius_px",
    "LODPolicy",
    "load_any_mesh",
    "extract_wireframe_edges",
    # mapping
    "VisualBinding",
    "VisualMap",
    "build_visual_map",
    "resolve_visual_binding",
]

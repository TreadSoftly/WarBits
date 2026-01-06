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
    from .blueprint_schema import (
        Blueprint,
        BlueprintGroup,
        BlueprintStyle,
        Edge,
        Meta,
        Node,
    )
    from .blueprint_db import BlueprintDB
    from .blueprint_lod import LODPolicy, select_edge_mask
    from .blueprint_transform import Transform3D, apply_transform
    from .registry import BlueprintRegistry
    from .mesh_io import load_mesh
    from .wireframe_extract import extract_wireframe
except Exception:  # pragma: no cover
    # Partial installs are allowed while iterating.
    pass

# Budgets / metrics (added later)
try:
    from .budgets import VisualBudgets
    from .metrics import VisualMetrics
except Exception:  # pragma: no cover
    pass

# Mapping layer
try:
    from .mapping import VisualBinding, VisualMap, build_visual_map, resolve_visual_binding
except Exception:  # pragma: no cover
    pass

__all__ = [
    # schema/db
    "Blueprint",
    "BlueprintGroup",
    "BlueprintStyle",
    "Node",
    "Edge",
    "Meta",
    "BlueprintDB",
    "BlueprintRegistry",
    "Transform3D",
    "apply_transform",
    "LODPolicy",
    "select_edge_mask",
    "load_mesh",
    "extract_wireframe",
    # budgets
    "VisualBudgets",
    "VisualMetrics",
    # mapping
    "VisualBinding",
    "VisualMap",
    "build_visual_map",
    "resolve_visual_binding",
]

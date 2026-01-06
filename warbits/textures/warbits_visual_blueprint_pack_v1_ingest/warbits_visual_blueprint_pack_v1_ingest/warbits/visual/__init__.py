"""WarBits Visual subsystem.

This package is intentionally renderer-agnostic.

It is for:
- loading source meshes (OBJ/GLB)
- extracting deterministic wireframe "blueprints"
- saving/loading blueprints (JSONL)
- providing preview tools (Matplotlib now; Panda3D later)

It is NOT for sim/physics logic.
"""

from .blueprint_schema import BlueprintRecord, BlueprintKind
from .blueprint_db import read_blueprints_jsonl, write_blueprints_jsonl
from .mesh_io import read_obj_objects, read_obj_mesh, load_gltf_scene_optional
from .wireframe_extract import extract_wireframe_edges

__all__ = [
    "BlueprintRecord",
    "BlueprintKind",
    "read_blueprints_jsonl",
    "write_blueprints_jsonl",
    "read_obj_objects",
    "read_obj_mesh",
    "load_gltf_scene_optional",
    "extract_wireframe_edges",
]

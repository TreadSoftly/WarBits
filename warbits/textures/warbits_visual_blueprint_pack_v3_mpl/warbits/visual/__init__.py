"""Visual blueprint subsystem (renderer-agnostic)."""

from .blueprint_db import (BlueprintDB, read_blueprints_jsonl,
                           write_blueprints_jsonl)
from .blueprint_schema import (Blueprint, BlueprintKind, BlueprintRecord,
                               Outline2D)
from .lod import LODPolicy
from .registry import VisualRegistry

__all__ = [
    "Blueprint",
    "BlueprintRecord",
    "BlueprintKind",
    "Outline2D",
    "BlueprintDB",
    "read_blueprints_jsonl",
    "write_blueprints_jsonl",
    "LODPolicy",
    "VisualRegistry",
]

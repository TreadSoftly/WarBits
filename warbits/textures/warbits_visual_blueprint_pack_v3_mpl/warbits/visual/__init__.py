"""Visual blueprint subsystem (renderer-agnostic)."""

from .blueprint_schema import Blueprint, BlueprintRecord, BlueprintKind, Outline2D
from .blueprint_db import BlueprintDB, read_blueprints_jsonl, write_blueprints_jsonl
from .lod import LODPolicy
from .registry import VisualRegistry

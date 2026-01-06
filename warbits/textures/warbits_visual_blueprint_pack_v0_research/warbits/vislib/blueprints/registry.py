from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Dict, Optional

from .schema import VisualBlueprint

@dataclass
class VisualRegistry:
    """Loads and resolves VisualBlueprint records.

    This is intentionally lightweight:
    - no renderer imports
    - no sim imports

    Typical usage:
    registry = VisualRegistry.from_json_file("assets/visual/blueprints/blueprints.json")
    bp = registry.get("f-35a")
    """

    blueprints: Dict[str, VisualBlueprint]

    def get(self, entity_id: str) -> Optional[VisualBlueprint]:
        return self.blueprints.get(entity_id)

    def require(self, entity_id: str) -> VisualBlueprint:
        bp = self.get(entity_id)
        if bp is None:
            raise KeyError(f"No visual blueprint for entity_id={entity_id!r}")
        return bp

    @staticmethod
    def from_json_file(path: str) -> "VisualRegistry":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        bps: Dict[str, VisualBlueprint] = {}
        for rec in data.get("blueprints", []):
            bp = VisualBlueprint.from_json(rec)
            bp.validate()
            bps[bp.entity_id] = bp
        return VisualRegistry(blueprints=bps)

    def to_json_file(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = {"blueprints": [bp.to_json() for bp in self.blueprints.values()]}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)

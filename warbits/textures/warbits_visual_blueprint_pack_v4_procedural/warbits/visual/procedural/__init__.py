"""Procedural blueprint generators.

These generators create *stylized but dimension-respecting* wireframe blueprints
for when you don't have a curated mesh blueprint for a vehicle/weapon yet.

Design goals:
- Deterministic: same params -> same vertices/edges.
- Cheap: small edge counts by default (LOD-friendly).
- Renderer-agnostic: output is Blueprint objects (vertices + edges + lod_edges).
- Not a CAD model: this is a readable tactical wireframe language.
"""

from .aircraft import JetParams  # type: ignore[reportUnknownVariableType]
from .aircraft import build_jet_blueprint  # type: ignore[reportUnknownVariableType]
from .aircraft import jet_params_from_spec  # type: ignore[reportUnknownVariableType]
from .dimensions import Dimensions, dims_from_mapping
from .ground import TankParams  # type: ignore[reportUnknownVariableType]
from .ground import build_tank_blueprint  # type: ignore[reportUnknownVariableType]
from .ground import tank_params_from_spec  # type: ignore[reportUnknownVariableType]
from .ordnance import BombParams  # type: ignore[reportUnknownVariableType]
from .ordnance import MissileParams  # type: ignore[reportUnknownVariableType]
from .ordnance import RocketParams  # type: ignore[reportUnknownVariableType]
from .ordnance import build_bomb_blueprint  # type: ignore[reportUnknownVariableType]
from .ordnance import build_missile_blueprint  # type: ignore[reportUnknownVariableType]
from .ordnance import build_rocket_blueprint  # type: ignore[reportUnknownVariableType]

__all__ = [
    "Dimensions",
    "dims_from_mapping",
    "JetParams",
    "build_jet_blueprint",
    "jet_params_from_spec",
    "TankParams",
    "build_tank_blueprint",
    "tank_params_from_spec",
    "MissileParams",
    "BombParams",
    "RocketParams",
    "build_missile_blueprint",
    "build_bomb_blueprint",
    "build_rocket_blueprint",
]

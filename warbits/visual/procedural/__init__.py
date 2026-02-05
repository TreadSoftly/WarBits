"""Procedural blueprint generators.

These generators create *stylized but dimension-respecting* wireframe blueprints
for when you don't have a curated mesh blueprint for a vehicle/weapon yet.

Design goals:
- Deterministic: same params -> same vertices/edges.
- Cheap: small edge counts by default (LOD-friendly).
- Renderer-agnostic: output is Blueprint objects (vertices + edges + lod_edges).
- Not a CAD model: this is a readable tactical wireframe language.
"""

from .aircraft import JetParams, build_jet_blueprint, jet_params_from_spec
from .dimensions import Dimensions, dims_from_mapping
from .ground import TankParams, build_tank_blueprint, tank_params_from_spec
from .ordnance import (
	BombParams,
	MissileParams,
	RocketParams,
	build_bomb_blueprint,
	build_missile_blueprint,
	build_rocket_blueprint,
)

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

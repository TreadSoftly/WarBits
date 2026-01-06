"""Procedural blueprint generators.

These generators create *stylized but dimension-respecting* wireframe blueprints
for when you don't have a curated mesh blueprint for a vehicle/weapon yet.

Design goals:
- Deterministic: same params -> same vertices/edges.
- Cheap: small edge counts by default (LOD-friendly).
- Renderer-agnostic: output is Blueprint objects (vertices + edges + lod_edges).
- Not a CAD model: this is a readable tactical wireframe language.
"""

from .dimensions import Dimensions, dims_from_mapping
from .aircraft import JetParams, build_jet_blueprint, jet_params_from_spec
from .ground import TankParams, build_tank_blueprint, tank_params_from_spec
from .ordnance import MissileParams, BombParams, RocketParams
from .ordnance import build_missile_blueprint, build_bomb_blueprint, build_rocket_blueprint

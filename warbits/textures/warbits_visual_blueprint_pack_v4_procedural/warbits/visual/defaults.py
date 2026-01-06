from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence, Union
import json

from .blueprint_db import BlueprintDB
from .blueprint_schema import Blueprint
from .procedural.aircraft import JetParams, build_jet_blueprint
from .procedural.ground import TankParams, build_tank_blueprint
from .procedural.ordnance import (
    MissileParams, RocketParams, BombParams,
    build_missile_blueprint, build_rocket_blueprint, build_bomb_blueprint,
)


@dataclass(frozen=True)
class DefaultBlueprintIds:
    """Canonical IDs for built-in procedural prototypes."""
    jet: str = "proc:aircraft:jet_generic"
    tank: str = "proc:ground:tank_generic"
    missile: str = "proc:ordnance:missile_generic"
    rocket: str = "proc:ordnance:rocket_generic"
    bomb: str = "proc:ordnance:bomb_generic"


def _db_put(db: BlueprintDB, bp: Blueprint) -> None:
    """Compatibility helper: support older/newer DB implementations."""
    if hasattr(db, "register"):
        db.register(bp)  # type: ignore[attr-defined]
        return
    # BlueprintDB (current) is a simple dict index.
    db.by_id[bp.blueprint_id] = bp


def load_blueprints_jsonl(db: BlueprintDB, path: Union[str, Path]) -> int:
    """Load Blueprint JSONL (one blueprint per line) into the DB."""
    p = Path(path)
    count = 0
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            bp = Blueprint.from_json(json.loads(line))
            _db_put(db, bp)
            count += 1
    return count


def build_default_blueprint_db(
    *,
    include_procedural: bool = True,
    extra_blueprints_jsonl: Optional[Sequence[Union[str, Path]]] = None,
) -> BlueprintDB:
    """Create a BlueprintDB with built-in procedural prototypes + optional extras."""
    db = BlueprintDB.empty() if hasattr(BlueprintDB, "empty") else BlueprintDB(by_id={})  # type: ignore

    if include_procedural:
        ids = DefaultBlueprintIds()
        _db_put(db, build_jet_blueprint(ids.jet, JetParams(), tags=["default", "generic"]))
        _db_put(db, build_tank_blueprint(ids.tank, TankParams(), tags=["default", "generic"]))
        _db_put(db, build_missile_blueprint(ids.missile, MissileParams(), tags=["default", "generic"]))
        _db_put(db, build_rocket_blueprint(ids.rocket, RocketParams(), tags=["default", "generic"]))
        _db_put(db, build_bomb_blueprint(ids.bomb, BombParams(), tags=["default", "generic"]))

    for p in (extra_blueprints_jsonl or []):
        load_blueprints_jsonl(db, p)

    return db

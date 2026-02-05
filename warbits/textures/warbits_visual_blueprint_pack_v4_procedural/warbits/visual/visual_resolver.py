from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional, Sequence, Set

from warbits.visual.blueprint_db import BlueprintDB
from warbits.visual.blueprint_schema import Blueprint

from .procedural.aircraft import build_jet_blueprint, jet_params_from_spec  # type: ignore[reportUnknownVariableType]
from .procedural.ground import build_tank_blueprint, tank_params_from_spec  # type: ignore[reportUnknownVariableType]
from .procedural.ordnance import build_bomb_blueprint  # type: ignore[reportUnknownVariableType]
from .procedural.ordnance import build_missile_blueprint  # type: ignore[reportUnknownVariableType]
from .procedural.ordnance import build_rocket_blueprint  # type: ignore[reportUnknownVariableType]
from .procedural.ordnance import BombParams, MissileParams, RocketParams


def _norm_str(x: Any) -> str:
    try:
        return str(x).strip().lower()
    except Exception:
        return ""


def _has_dims(spec: Mapping[str, Any]) -> bool:
    """Return True if the spec contains any numeric dimension hints."""
    for k in (
        "length_m",
        "wingspan_m",
        "width_m",
        "height_m",
        "diameter_m",
        "length",
        "wingspan",
        "width",
        "height",
        "diameter",
        "caliber",
    ):
        if k in spec and spec[k] is not None:
            try:
                v = float(spec[k])
            except Exception:
                continue
            if v > 0.0:
                return True
    return False


def infer_kind(spec: Mapping[str, Any], *, hint: Optional[str] = None) -> str:
    """Infer a visual kind from a spec mapping.

    Returns one of: "aircraft", "ground", "ordnance", "unknown".

    Best practice:
    - add a stable field like spec["visual_kind"] in your normalized JSON;
      then this becomes deterministic and fast.
    """
    if hint:
        h = _norm_str(hint)
        if h in ("aircraft", "ground", "ordnance"):
            return h

    for key in ("visual_kind", "kind", "domain"):
        if key in spec:
            k = _norm_str(spec.get(key))
            if k in ("aircraft", "ground", "ordnance"):
                return k

    blob = " ".join(
        [
            _norm_str(spec.get("type")),
            _norm_str(spec.get("class")),
            _norm_str(spec.get("category")),
            _norm_str(spec.get("role")),
            _norm_str(spec.get("name")),
            _norm_str(spec.get("vehicle")),
            _norm_str(spec.get("weapon")),
        ]
    )

    if any(w in blob for w in ("aircraft", "plane", "jet", "fighter", "bomber", "helicopter", "heli")):
        return "aircraft"
    if any(w in blob for w in ("missile", "rocket", "bomb", "torpedo", "shell", "round", "bullet", "warhead")):
        return "ordnance"
    if any(w in blob for w in ("tank", "apc", "ifv", "truck", "ground", "vehicle", "sam", "spaa", "artillery")):
        return "ground"

    return "unknown"


def infer_ordnance_subkind(spec: Mapping[str, Any]) -> str:
    blob = " ".join(
        [
            _norm_str(spec.get("type")),
            _norm_str(spec.get("category")),
            _norm_str(spec.get("name")),
        ]
    )
    if "bomb" in blob:
        return "bomb"
    if "rocket" in blob:
        return "rocket"
    return "missile"


def _db_get(db: BlueprintDB, blueprint_id: str) -> Optional[Blueprint]:
    if hasattr(db, "get"):
        return db.get(blueprint_id)  # type: ignore[attr-defined]
    return db.by_id.get(blueprint_id)


def _db_put(db: BlueprintDB, bp: Blueprint) -> None:
    if hasattr(db, "register"):
        db.register(bp)  # type: ignore[attr-defined]
        return
    db.by_id[bp.blueprint_id] = bp


def _db_iter(db: BlueprintDB) -> Iterable[Optional[Blueprint]]:
    if hasattr(db, "by_id"):
        return db.by_id.values()
    if hasattr(db, "ids"):
        return (_db_get(db, i) for i in db.ids())  # type: ignore[attr-defined]
    return []


def _best_for(db: BlueprintDB, *, kind: str, required_tags: Set[str]) -> Optional[Blueprint]:
    """Select best matching blueprint by (kind + required tag subset).

    Deterministic selection rule:
    - candidates must contain *all* required_tags
    - choose the candidate with the most total tags (usually the most specific)
    """
    best: Optional[Blueprint] = None
    best_score = -1

    for bp in _db_iter(db):
        if bp is None:
            continue
        if bp.kind != kind:
            continue
        bp_tags = set(getattr(bp, "tags", []) or [])
        if not required_tags.issubset(bp_tags):
            continue
        score = len(bp_tags)
        if score > best_score:
            best = bp
            best_score = score

    return best


@dataclass
class VisualResolver:
    """Resolve a vehicle/weapon spec to a Blueprint.

    Strategy:
      1) exact match by entity_id (fast path)
      2) prototype match (when dimensions are missing)
      3) procedural generation (coverage + dimension-respecting)
    """

    db: BlueprintDB
    allow_generate: bool = True

    def resolve(
        self,
        entity_id: str,
        spec: Mapping[str, Any],
        *,
        hint_kind: Optional[str] = None,
        tags: Optional[Sequence[str]] = None,
    ) -> Blueprint:
        # 1) Exact match by entity ID
        if entity_id:
            hit = _db_get(self.db, entity_id)
            if hit is not None:
                return hit

        kind = infer_kind(spec, hint=hint_kind)
        has_dims = _has_dims(spec)

        # 2) Prototype match by kind+tags
        # If we have dimensions, prefer generating per-entity so proportions are right.
        use_prototypes = (not has_dims) or (not entity_id)
        if use_prototypes and kind != "unknown":
            req: Set[str] = set(tags or [])
            req.add(kind)
            best = _best_for(self.db, kind=kind, required_tags=req)
            if best is not None:
                return best

        # 3) Procedural fallback
        if not self.allow_generate:
            raise KeyError(f"No blueprint for {entity_id!r} (kind={kind}) and generation disabled")

        out_id = entity_id or f"proc:{kind}:{_norm_str(spec.get('name')) or 'unknown'}"

        if kind == "aircraft":
            p = jet_params_from_spec(spec)
            bp = build_jet_blueprint(out_id, p, tags=tags)
            _db_put(self.db, bp)
            return bp

        if kind == "ground":
            p = tank_params_from_spec(spec)
            bp = build_tank_blueprint(out_id, p, tags=tags)
            _db_put(self.db, bp)
            return bp

        if kind == "ordnance":
            sub = infer_ordnance_subkind(spec)
            if sub == "bomb":
                bp = build_bomb_blueprint(out_id, BombParams(), tags=tags)
            elif sub == "rocket":
                bp = build_rocket_blueprint(out_id, RocketParams(), tags=tags)
            else:
                bp = build_missile_blueprint(out_id, MissileParams(), tags=tags)
            _db_put(self.db, bp)
            return bp

        # Unknown -> ground proxy (boxy silhouette)
        p = tank_params_from_spec(spec)
        bp = build_tank_blueprint(out_id, p, tags=(list(tags or []) + ["unknown"]))
        _db_put(self.db, bp)
        return bp

        # Unknown -> ground proxy (boxy silhouette)
        p = tank_params_from_spec(spec)
        bp = build_tank_blueprint(out_id, p, tags=(list(tags or []) + ["unknown"]))
        _db_put(self.db, bp)
        return bp
        # Unknown -> ground proxy (boxy silhouette)
        p = tank_params_from_spec(spec)
        bp = build_tank_blueprint(out_id, p, tags=(list(tags or []) + ["unknown"]))
        _db_put(self.db, bp)
        return bp

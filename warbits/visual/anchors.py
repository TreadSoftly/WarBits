from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple
import json

import numpy as np
import numpy.typing as npt
from typing import cast


NDArrayF = npt.NDArray[np.float64]
AnchorMap = Dict[str, NDArrayF]


@dataclass(frozen=True)
class AnchorRecord:
    """
    A single blueprint's anchor set.

    - All anchors are in *local blueprint space* (before pose/scale).
    - Convention: x=forward, y=left, z=up (matches simlib math3d in packs).
    """
    blueprint_id: str
    anchors: AnchorMap
    kind_hint: Optional[str] = None  # e.g., "vehicle.aircraft", "vehicle.ground", "weapon.missile"


class AnchorDB:
    """
    Lightweight JSONL store:
        {"blueprint_id":"mesh:foo","anchors":{"nose":[1,0,0], ...}, "kind_hint":"vehicle.aircraft"}

    Designed so you can:
    - auto-generate anchors for everything
    - then hand-override only what matters
    """

    def __init__(self, records: Optional[Mapping[str, AnchorRecord]] = None):
        self._records: Dict[str, AnchorRecord] = dict(records) if records else {}

    @classmethod
    def load_jsonl(cls, path: str | Path) -> "AnchorDB":
        p = Path(path)
        records: Dict[str, AnchorRecord] = {}
        if not p.exists():
            return cls(records)

        with p.open("r", encoding="utf-8") as f:
            for ln, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON on line {ln} of {p}: {e}") from e

                bid = str(obj.get("blueprint_id", "")).strip()
                if not bid:
                    raise ValueError(f"Missing blueprint_id on line {ln} of {p}")

                anchors_obj = obj.get("anchors", {})
                if not isinstance(anchors_obj, dict):
                    raise ValueError(f"anchors must be an object on line {ln} of {p}")

                anchors: AnchorMap = {}
                for k, v in anchors_obj.items():
                    if not isinstance(k, str):
                        continue
                    arr = cast(NDArrayF, np.asarray(v, dtype=np.float64))
                    if arr.shape != (3,):
                        raise ValueError(f"Anchor '{k}' must be a 3-vector on line {ln} of {p}")
                    anchors[k] = arr

                kind_hint = obj.get("kind_hint")
                kind_hint = str(kind_hint).strip() if kind_hint is not None else None

                records[bid] = AnchorRecord(blueprint_id=bid, anchors=anchors, kind_hint=kind_hint)

        return cls(records)

    def save_jsonl(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8") as f:
            for bid in sorted(self._records.keys()):
                rec = self._records[bid]
                obj = {
                    "blueprint_id": rec.blueprint_id,
                    "anchors": {k: rec.anchors[k].tolist() for k in sorted(rec.anchors.keys())},
                }
                if rec.kind_hint:
                    obj["kind_hint"] = rec.kind_hint
                f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    def get(self, blueprint_id: str) -> Optional[AnchorRecord]:
        return self._records.get(blueprint_id)

    def upsert(self, record: AnchorRecord) -> None:
        self._records[record.blueprint_id] = record

    def delete(self, blueprint_id: str) -> None:
        self._records.pop(blueprint_id, None)

    def blueprint_ids(self) -> List[str]:
        return sorted(self._records.keys())


def _infer_kind(blueprint_id: str, kind_hint: Optional[str], meta_kind: Optional[str]) -> str:
    """
    Heuristic only. The core rule is: we *prefer* explicit kind_hint, then meta_kind,
    and only then do a crude string guess based on blueprint_id.
    """
    if kind_hint:
        return kind_hint
    if meta_kind:
        return meta_kind

    bid = blueprint_id.lower()

    # air
    if any(t in bid for t in ["aircraft", "plane", "jet", "helicopter", "heli", "uav", "drone"]):
        return "vehicle.aircraft"

    # ground
    if any(t in bid for t in ["tank", "apc", "ifv", "spaa", "sam", "truck", "ground"]):
        return "vehicle.ground"

    # sea
    if any(t in bid for t in ["ship", "boat", "destroyer", "frigate", "carrier", "sub"]):
        return "vehicle.sea"

    # ordnance
    if any(t in bid for t in ["missile", "rocket", "bomb", "shell", "bullet", "torpedo", "ordnance", "weapon"]):
        return "weapon"

    return "unknown"


def compute_default_anchors(
    *,
    blueprint_id: str,
    vertices_m: np.ndarray,
    kind_hint: Optional[str] = None,
    meta_kind: Optional[str] = None,
) -> AnchorMap:
    """
    Generate a *useful* baseline anchor set from the blueprint's bounds.

    These anchors are intentionally simple and deterministic.
    Later you override with AnchorDB for high-fidelity mounting.
    """
    V = cast(NDArrayF, np.asarray(vertices_m, dtype=np.float64))
    if V.ndim != 2 or V.shape[1] != 3 or V.shape[0] < 2:
        raise ValueError("vertices_m must be (N,3) with N>=2")

    vmin = V.min(axis=0)
    vmax = V.max(axis=0)
    dims = vmax - vmin
    center = 0.5 * (vmin + vmax)

    kind = _infer_kind(blueprint_id, kind_hint, meta_kind).lower()

    # helpers for normalized bbox points
    def p(nx: float, ny: float, nz: float) -> NDArrayF:
        # nx,ny,nz in [0,1] relative bbox
        return cast(NDArrayF, vmin + np.array([nx, ny, nz], dtype=np.float64) * dims)

    anchors: AnchorMap = {
        "center": center.copy(),
        "bbox_min": vmin.copy(),
        "bbox_max": vmax.copy(),
        "front": p(1.0, 0.5, 0.5),
        "rear":  p(0.0, 0.5, 0.5),
        "left":  p(0.5, 1.0, 0.5),
        "right": p(0.5, 0.0, 0.5),
        "top":   p(0.5, 0.5, 1.0),
        "bottom":p(0.5, 0.5, 0.0),
    }

    # Aircraft-ish: provide wing- and pylon-ish anchors
    if "vehicle.aircraft" in kind or ("vehicle" in kind and "air" in kind):
        anchors.update({
            "nose": p(1.0, 0.5, 0.55),
            "tail": p(0.0, 0.5, 0.55),
            "left_wing_tip":  p(0.55, 1.0, 0.45),
            "right_wing_tip": p(0.55, 0.0, 0.45),

            # Generic pylons under wings, closer to center
            "pylon_left_1":  p(0.55, 0.80, 0.25),
            "pylon_left_2":  p(0.50, 0.65, 0.25),
            "pylon_right_1": p(0.55, 0.20, 0.25),
            "pylon_right_2": p(0.50, 0.35, 0.25),

            "centerline_hardpoint": p(0.45, 0.50, 0.20),
        })

    # Ground-ish: turret / barrel-ish anchor
    if "vehicle.ground" in kind or ("vehicle" in kind and "ground" in kind):
        anchors.update({
            "turret_pivot": p(0.55, 0.50, 0.75),
            "gun_muzzle":   p(1.0, 0.50, 0.70),
            "left_track_mid":  p(0.50, 0.98, 0.20),
            "right_track_mid": p(0.50, 0.02, 0.20),
        })

    # Weapon-ish (missile/bomb): nose/tail
    if kind.startswith("weapon") or kind == "weapon":
        anchors.update({
            "weapon_nose": p(1.0, 0.5, 0.5),
            "weapon_tail": p(0.0, 0.5, 0.5),
            "weapon_mount": p(0.5, 0.5, 0.5),
        })

    # Always provide a sensible "mount" anchor (children attach here by default).
    if "mount" not in anchors:
        anchors["mount"] = center.copy()

    return anchors


def merge_anchor_maps(base: AnchorMap, override: AnchorMap) -> AnchorMap:
    """
    Override wins on name collisions.
    """
    out = dict(base)
    out.update({k: cast(NDArrayF, np.asarray(v, dtype=np.float64).reshape(3,)) for k, v in override.items()})
    return out

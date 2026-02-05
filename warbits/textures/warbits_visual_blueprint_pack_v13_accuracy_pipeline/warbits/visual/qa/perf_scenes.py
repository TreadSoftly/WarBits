from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union, cast

import numpy as np
from numpy.typing import NDArray

PathLike = Union[str, Path]


@dataclass
class PerfSceneResult:
    name: str
    frames: int
    total_ms: float
    avg_ms: float
    segments_built: int
    hash64: str


def _hash64(arr: NDArray[np.float_]) -> str:
    """Deterministic hash for perf-regression output.

    This is NOT cryptographically secure. It is only used to prove
    "same inputs -> same geometry" for CI and regression testing.
    """
    b = np.frombuffer(arr.tobytes(order="C"), dtype=np.uint8)
    # pad to 8-byte boundary
    pad = (-len(b)) % 8
    if pad:
        b = np.concatenate([b, np.zeros(pad, dtype=np.uint8)])
    u = np.frombuffer(b.tobytes(), dtype=np.uint64)
    x = np.uint64(0)
    for v in u:
        x ^= v
        x = (x * np.uint64(0x9E3779B97F4A7C15)) & np.uint64(0xFFFFFFFFFFFFFFFF)
    return hex(int(x))


def load_blueprints_jsonl(path: PathLike) -> Dict[str, Dict[str, Any]]:
    p = Path(path)
    out: Dict[str, Dict[str, Any]] = {}
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if not isinstance(rec, dict):
                continue
            rec_map = cast(Dict[str, Any], rec)
            bid = rec_map.get("blueprint_id") or rec_map.get("id")
            if not isinstance(bid, str) or not bid:
                continue
            out[bid] = rec_map
    return out


def _as_np_geometry(rec: Dict[str, Any], lod: str) -> Tuple[NDArray[np.float_], NDArray[np.int_]]:
    verts = rec.get("vertices_m") or rec.get("vertices")
    edges = rec.get("edges")
    lod_edges_raw = cast(Dict[str, Any], rec.get("lod_edges") or rec.get("lod") or {})
    if lod in lod_edges_raw:
        edges = lod_edges_raw[lod]
    V = np.asarray(verts, dtype=np.float32)
    E = np.asarray(edges, dtype=np.int32)
    if V.ndim != 2 or V.shape[1] != 3:
        raise ValueError("bad vertices")
    if E.ndim != 2 or E.shape[1] != 2:
        raise ValueError("bad edges")
    return V, E


def _select_lod(distance_m: float) -> str:
    if distance_m < 250:
        return "lod0"
    if distance_m < 900:
        return "lod1"
    if distance_m < 2500:
        return "lod2"
    return "lod3"


def _random_rot(rng: np.random.Generator) -> NDArray[np.float_]:
    # Random yaw/pitch/roll (small pitch/roll)
    yaw = float(rng.uniform(-np.pi, np.pi))
    pitch = float(rng.uniform(-0.25, 0.25))
    roll = float(rng.uniform(-0.25, 0.25))
    cy, sy = np.cos(yaw), np.sin(yaw)
    cp, sp = np.cos(pitch), np.sin(pitch)
    cr, sr = np.cos(roll), np.sin(roll)
    Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]], dtype=np.float32)
    Ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]], dtype=np.float32)
    Rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]], dtype=np.float32)
    return (Rz @ Ry @ Rx).astype(np.float32)


def run_perf_scene(
    name: str,
    blueprints: Dict[str, Dict[str, Any]],
    blueprint_id: str,
    frames: int,
    instances: int,
    seed: int,
    out_path: Optional[PathLike] = None,
) -> PerfSceneResult:
    """Build wireframe segments for many instances for N frames.

    This does not render. It's a CPU-side stress test for the geometry/update path.
    """
    rng = np.random.default_rng(seed)
    if blueprint_id not in blueprints:
        raise KeyError(f"blueprint_id not found: {blueprint_id}")

    # Pre-generate instance poses.
    pos = cast(Any, rng.normal(size=(instances, 3)).astype(np.float32))
    pos[:, 2] = np.abs(pos[:, 2]) * 200.0 + 50.0
    pos *= 800.0
    rot_list = cast(list[Any], [_random_rot(rng) for _ in range(instances)])
    rots = cast(Any, np.stack(rot_list, axis=0))
    scales = cast(Any, rng.random(instances))
    scales = (0.85 + 0.3 * scales).astype(np.float32)

    # Cache geometry per LOD.
    rec = blueprints[blueprint_id]
    geom_by_lod: Dict[str, Tuple[NDArray[np.float_], NDArray[np.int_]]] = {}
    for lod in ["lod0", "lod1", "lod2", "lod3"]:
        try:
            geom_by_lod[lod] = _as_np_geometry(rec, lod)
        except Exception:
            # some DBs might not have all LODs
            pass

    # Worst-case allocate buffer: max edges of lod0.
    V0, E0 = geom_by_lod.get("lod0") or _as_np_geometry(rec, "lod0")
    max_edges = int(E0.shape[0])
    seg_buf = cast(Any, np.empty((instances * max_edges, 2, 3), dtype=np.float32))

    t0 = time.perf_counter_ns()
    seg_total = 0

    cursor = 0
    for fi in range(frames):
        # Move camera in a circle to exercise LOD switching.
        cam = np.array(
            [
                1200.0 * np.cos(0.02 * fi),
                1200.0 * np.sin(0.02 * fi),
                600.0,
            ],
            dtype=np.float32,
        )

        cursor = 0
        for i in range(instances):
            d = float(np.linalg.norm(pos[i] - cam))
            lod = _select_lod(d)
            V, E = geom_by_lod.get(lod, (V0, E0))

            # Transform vertices: (3,3) @ (3,N) -> (3,N)
            v = (rots[i] @ (V.T * scales[i])).T + pos[i]
            seg = v[E]  # (M,2,3)
            m = seg.shape[0]
            seg_buf[cursor : cursor + m] = seg
            cursor += m

        seg_total += cursor

    t1 = time.perf_counter_ns()
    total_ms = (t1 - t0) / 1e6
    avg_ms = total_ms / max(frames, 1)

    # Hash of the *last* frame's segments slice.
    last_slice = seg_buf[: min(cursor, seg_buf.shape[0])]
    h = _hash64(cast(NDArray[np.float_], last_slice))

    result = PerfSceneResult(
        name=name,
        frames=frames,
        total_ms=float(total_ms),
        avg_ms=float(avg_ms),
        segments_built=int(seg_total),
        hash64=h,
    )

    if out_path is not None:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_text(json.dumps(result.__dict__, indent=2, sort_keys=True), encoding="utf-8")

    return result


def run_default_perfreg(
    blueprints_jsonl: PathLike,
    out_json: Optional[PathLike] = None,
    frames: int = 30,
    seed: int = 7,
) -> Dict[str, Any]:
    """Run a small perf regression harness and write a report."""
    db = load_blueprints_jsonl(blueprints_jsonl)
    if not db:
        raise ValueError("No blueprints found")

    # Choose a stable default blueprint: prefer a 'proc:' fallback if present, else first.
    candidates = list(db.keys())
    pick = next((k for k in candidates if k.startswith("proc:")), candidates[0])

    scene_a = run_perf_scene(
        name="A_many_entities",
        blueprints=db,
        blueprint_id=pick,
        frames=frames,
        instances=200,
        seed=seed,
    )
    scene_b = run_perf_scene(
        name="B_lod_stress",
        blueprints=db,
        blueprint_id=pick,
        frames=frames,
        instances=2000,
        seed=seed + 1,
    )

    report: Dict[str, Any] = {
        "blueprints_jsonl": str(blueprints_jsonl),
        "picked_blueprint": pick,
        "frames": int(frames),
        "seed": int(seed),
        "scenes": {
            scene_a.name: scene_a.__dict__,
            scene_b.name: scene_b.__dict__,
        },
    }

    if out_json is not None:
        outp = Path(out_json)
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    return report


# Back-compat alias: some callers use this name.
def run_perf_regression(blueprints_jsonl: PathLike, frames: int = 200, seed: int = 7):
    """Return raw scene results (list), without writing files.

    This is the API tests and interactive workflows tend to want.
    For the JSON report used by the CLI, use `run_default_perfreg(...)`.
    """
    db = load_blueprints_jsonl(blueprints_jsonl)
    if not db:
        raise ValueError("No blueprints found")

    candidates = list(db.keys())
    pick = next((k for k in candidates if k.startswith("proc:")), candidates[0])

    scene_a = run_perf_scene(
        name="A_many_entities",
        blueprints=db,
        blueprint_id=pick,
        frames=frames,
        instances=200,
        seed=seed,
    )
    scene_b = run_perf_scene(
        name="B_lod_stress",
        blueprints=db,
        blueprint_id=pick,
        frames=frames,
        instances=2000,
        seed=seed + 1,
    )

    return [scene_a, scene_b]

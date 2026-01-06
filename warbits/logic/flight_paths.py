# ── warbits/logic/flight_paths.py ───────────────────────────────────────────
from __future__ import annotations
# Flight-path generator (moved here from physics/).

import math
import random
from typing import Dict, Tuple

import numpy as np
from numpy.typing import NDArray

from ..config import settings as _cfg

__all__ = [
    "DEFAULT_PHASES",
    "generate_path",
    "build_flight_plan",
    "build_flight_plan_variant",
]

_PHASE_ORDER = ("Approach", "Strafe", "Bombing", "Escape", "Dogfight")

# ────────────────────────────────────────────────────────────────────────────
# 1 · Canonical phase table
# ────────────────────────────────────────────────────────────────────────────
DEFAULT_PHASES: dict[str, Tuple[str, int]] = {
    "Approach": ("blue",    60),
    "Strafe":   ("orange",  50),
    "Bombing":  ("red",     40),
    "Escape":   ("green",   60),
    "Dogfight": ("purple",  70),
}


def _normalize_phases(phases: dict[str, Tuple[str, int]]) -> dict[str, Tuple[str, int]]:
    normalized: dict[str, Tuple[str, int]] = {}
    for name in _PHASE_ORDER:
        if name in phases:
            color, count = phases[name]
        else:
            color, count = DEFAULT_PHASES[name]
        try:
            count_int = int(count)
        except (TypeError, ValueError):
            count_int = int(DEFAULT_PHASES[name][1])
        if count_int < 2:
            count_int = 2
        normalized[name] = (color, count_int)
    return normalized

# ────────────────────────────────────────────────────────────────────────────
# 2 · Low-level segment generator
# ────────────────────────────────────────────────────────────────────────────
def generate_path(
    start: tuple[float, float, float],
    end:   tuple[float, float, float],
    num_points: int,
    *,
    curve: str = "",
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Return evenly-spaced XYZ arrays between *start* and *end*."""
    if num_points < 2:
        raise ValueError("num_points must be ≥ 2")

    x0, y0, z0 = start
    x1, y1, z1 = end
    t = np.linspace(0.0, 1.0, num_points, dtype=np.float64)

    x = x0 + (x1 - x0) * t
    y = y0 + (y1 - y0) * t
    z = z0 + (z1 - z0) * t

    if curve == "strafe_dive":
        z = z0 - (z0 - z1) * np.sin(t * math.pi / 2.0)
    elif curve == "escape_climb":
        z += 500.0 * np.sin(2.0 * math.pi * t)
    elif curve == "dogfight_maneuver":
        x += 400.0 * np.sin(2.0 * math.pi * t)
        y += 300.0 * np.sin(3.0 * math.pi * t)
        z += 200.0 * np.sin(2.0 * math.pi * t)

    return x, y, z


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _scene_bounds() -> tuple[
    tuple[float, float],
    tuple[float, float],
    tuple[float, float],
]:
    x_min = float(_cfg.TERRAIN_XMIN)
    x_max = float(_cfg.TERRAIN_XMAX)
    y_min = float(_cfg.TERRAIN_YMIN)
    y_max = float(_cfg.TERRAIN_YMAX)
    span_x = max(1.0, x_max - x_min)
    span_y = max(1.0, y_max - y_min)
    margin = max(200.0, 0.05 * min(span_x, span_y))
    if (x_max - x_min) > (2.0 * margin):
        x_min += margin
        x_max -= margin
    if (y_max - y_min) > (2.0 * margin):
        y_min += margin
        y_max -= margin
    z_min = float(_cfg.TERRAIN_ZMIN)
    z_max = float(_cfg.TERRAIN_ZMAX)
    return (x_min, x_max), (y_min, y_max), (z_min, z_max)


def _clamp_point(
    point: tuple[float, float, float],
    bounds: tuple[tuple[float, float], tuple[float, float], tuple[float, float]],
) -> tuple[float, float, float]:
    return (
        _clamp(point[0], bounds[0][0], bounds[0][1]),
        _clamp(point[1], bounds[1][0], bounds[1][1]),
        _clamp(point[2], bounds[2][0], bounds[2][1]),
    )


def _edge_point(
    edge: str,
    bounds: tuple[tuple[float, float], tuple[float, float], tuple[float, float]],
    *,
    rng: random.Random,
    altitude: float,
) -> tuple[float, float, float]:
    (x_min, x_max), (y_min, y_max), _ = bounds
    span_x = max(1.0, x_max - x_min)
    span_y = max(1.0, y_max - y_min)
    inset = max(400.0, 0.12 * min(span_x, span_y))
    if span_x > 2.0 * inset:
        x_min += inset
        x_max -= inset
    if span_y > 2.0 * inset:
        y_min += inset
        y_max -= inset
    if edge == "west":
        x = x_min
        y = rng.uniform(y_min, y_max)
    elif edge == "east":
        x = x_max
        y = rng.uniform(y_min, y_max)
    elif edge == "north":
        x = rng.uniform(x_min, x_max)
        y = y_max
    else:
        x = rng.uniform(x_min, x_max)
        y = y_min
    return _clamp_point((x, y, altitude), bounds)


def _edge_from_point(
    point: tuple[float, float, float],
    bounds: tuple[tuple[float, float], tuple[float, float], tuple[float, float]],
) -> str:
    (x_min, x_max), (y_min, y_max), _ = bounds
    x, y, _ = point
    distances = {
        "west": abs(x - x_min),
        "east": abs(x_max - x),
        "south": abs(y - y_min),
        "north": abs(y_max - y),
    }
    return min(distances, key=lambda key: distances[key])


def _choose_edge_for_target(
    rng: random.Random,
    target_xy: tuple[float, float],
    bounds: tuple[tuple[float, float], tuple[float, float], tuple[float, float]],
) -> str:
    (x_min, x_max), (y_min, y_max), _ = bounds
    tx = _clamp(target_xy[0], x_min, x_max)
    ty = _clamp(target_xy[1], y_min, y_max)
    distances = {
        "west": max(1.0, tx - x_min),
        "east": max(1.0, x_max - tx),
        "south": max(1.0, ty - y_min),
        "north": max(1.0, y_max - ty),
    }
    weights = {edge: dist * dist for edge, dist in distances.items()}
    total = sum(weights.values())
    if total <= 0.0:
        return rng.choice(["west", "east", "north", "south"])
    roll = rng.random() * total
    for edge, weight in weights.items():
        roll -= weight
        if roll <= 0.0:
            return edge
    return "west"


def _altitudes(
    rng: random.Random,
    bounds: tuple[tuple[float, float], tuple[float, float], tuple[float, float]],
    *,
    variant: str | None,
) -> tuple[float, float, float]:
    z_min, z_max = bounds[2]
    span = max(1.0, z_max - z_min)
    low = z_min + 0.10 * span
    mid = z_min + 0.30 * span
    high = z_min + 0.65 * span
    if variant == "high_alt":
        low += 0.10 * span
        mid += 0.12 * span
        high += 0.15 * span
    elif variant == "low_alt":
        low -= 0.05 * span
        mid -= 0.08 * span
        high -= 0.10 * span
    low = _clamp(low, z_min + 100.0, z_max - 500.0)
    mid = _clamp(mid, z_min + 200.0, z_max - 400.0)
    high = _clamp(high, z_min + 400.0, z_max - 200.0)
    low += rng.uniform(-0.03 * span, 0.03 * span)
    mid += rng.uniform(-0.04 * span, 0.04 * span)
    high += rng.uniform(-0.05 * span, 0.05 * span)
    return (
        _clamp(low, z_min + 100.0, z_max - 500.0),
        _clamp(mid, z_min + 200.0, z_max - 400.0),
        _clamp(high, z_min + 400.0, z_max - 200.0),
    )


def _dynamic_points(
    rng: random.Random,
    variant: str | None,
    *,
    bounds: tuple[tuple[float, float], tuple[float, float], tuple[float, float]],
    target_xy: tuple[float, float] | None,
    secondary_xy: tuple[float, float] | None,
    start_pos: tuple[float, float, float] | None,
) -> tuple[
    tuple[float, float, float],
    tuple[float, float, float],
    tuple[float, float, float],
    tuple[float, float, float],
    tuple[float, float, float],
    tuple[float, float, float],
]:
    (x_min, x_max), (y_min, y_max), _ = bounds
    span_x = max(1.0, x_max - x_min)
    span_y = max(1.0, y_max - y_min)
    center_x = (x_min + x_max) / 2.0
    center_y = (y_min + y_max) / 2.0

    style = variant or ""
    bias_x = 0.0
    bias_y = 0.0
    edge = ""
    if style == "wide_east":
        bias_x = 0.20 * span_x
        edge = "west"
    elif style == "tight_west":
        bias_x = -0.20 * span_x
        edge = "east"
    elif style == "north_arc":
        bias_y = 0.20 * span_y
    elif style == "south_arc":
        bias_y = -0.20 * span_y

    if start_pos is not None:
        edge = _edge_from_point(start_pos, bounds)
    elif not edge:
        if target_xy is not None:
            edge = _choose_edge_for_target(rng, target_xy, bounds)
        else:
            edge = rng.choice(["west", "east", "north", "south"])

    opposite = {
        "west": "east",
        "east": "west",
        "north": "south",
        "south": "north",
    }[edge]

    z_low, z_mid, z_high = _altitudes(rng, bounds, variant=variant)

    if target_xy is None:
        target_x = center_x + bias_x + rng.uniform(-0.30 * span_x, 0.30 * span_x)
        target_y = center_y + bias_y + rng.uniform(-0.30 * span_y, 0.30 * span_y)
    else:
        anchor_x = (0.65 * target_xy[0]) + (0.35 * center_x)
        anchor_y = (0.65 * target_xy[1]) + (0.35 * center_y)
        target_x = anchor_x + bias_x + rng.uniform(-0.20 * span_x, 0.20 * span_x)
        target_y = anchor_y + bias_y + rng.uniform(-0.20 * span_y, 0.20 * span_y)
    edge_margin_x = max(200.0, 0.12 * span_x)
    edge_margin_y = max(200.0, 0.12 * span_y)
    if span_x <= 2.0 * edge_margin_x:
        edge_margin_x = 0.04 * span_x
    if span_y <= 2.0 * edge_margin_y:
        edge_margin_y = 0.04 * span_y
    target_xy = (
        _clamp(target_x, x_min + edge_margin_x, x_max - edge_margin_x),
        _clamp(target_y, y_min + edge_margin_y, y_max - edge_margin_y),
    )

    if start_pos is None:
        a0 = _edge_point(edge, bounds, rng=rng, altitude=z_high)
    else:
        a0 = _clamp_point(start_pos, bounds)

    dir_x = target_xy[0] - a0[0]
    dir_y = target_xy[1] - a0[1]
    dir_len = math.hypot(dir_x, dir_y)
    if dir_len < 1.0e-3:
        dir_x, dir_y, dir_len = 1.0, 0.0, 1.0
    dir_x /= dir_len
    dir_y /= dir_len
    perp_x, perp_y = -dir_y, dir_x

    run_span = min(span_x, span_y)
    approach = rng.uniform(0.10 * run_span, 0.22 * run_span)
    max_approach = max(120.0, 0.70 * dir_len)
    approach = min(approach, max_approach)
    if approach > 0.90 * dir_len:
        approach = 0.60 * dir_len

    exit_dist = rng.uniform(0.12 * run_span, 0.26 * run_span)
    lateral = rng.uniform(-0.06 * run_span, 0.06 * run_span)

    line_x = target_xy[0] - dir_x * (approach * 0.55)
    line_y = target_xy[1] - dir_y * (approach * 0.55)
    if secondary_xy is not None:
        line_x = (0.70 * secondary_xy[0]) + (0.30 * line_x)
        line_y = (0.70 * secondary_xy[1]) + (0.30 * line_y)

    a1 = _clamp_point(
        (
            line_x + perp_x * lateral,
            line_y + perp_y * lateral,
            z_mid,
        ),
        bounds,
    )
    b1 = _clamp_point(
        (
            target_xy[0] - dir_x * approach,
            target_xy[1] - dir_y * approach,
            z_low,
        ),
        bounds,
    )
    c1 = _clamp_point(
        (
            target_xy[0] + dir_x * exit_dist,
            target_xy[1] + dir_y * exit_dist,
            z_low + rng.uniform(50.0, 180.0),
        ),
        bounds,
    )
    d1 = _edge_point(opposite, bounds, rng=rng, altitude=z_high)
    e1 = _clamp_point(
        (
            center_x + rng.uniform(-0.45 * span_x, 0.45 * span_x),
            center_y + rng.uniform(-0.45 * span_y, 0.45 * span_y),
            z_high,
        ),
        bounds,
    )
    return a0, a1, b1, c1, d1, e1


def _segment_points(
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    count: int,
    *,
    curve: str = "",
    rng: random.Random | None,
    bounds: tuple[tuple[float, float], tuple[float, float], tuple[float, float]],
    prev: tuple[float, float, float] | None = None,
    next: tuple[float, float, float] | None = None,
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    apply_curve = False
    if prev is not None and next is not None and count >= 4:
        t = np.linspace(0.0, 1.0, count, dtype=np.float64)
        t2 = t * t
        t3 = t2 * t
        p0 = np.array(prev, dtype=np.float64)
        p1 = np.array(start, dtype=np.float64)
        p2 = np.array(end, dtype=np.float64)
        p3 = np.array(next, dtype=np.float64)
        pts = (
            0.5
            * (
                (2.0 * p1)
                + (-p0 + p2) * t[:, None]
                + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t2[:, None]
                + (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t3[:, None]
            )
        )
        x = pts[:, 0]
        y = pts[:, 1]
        z = pts[:, 2]
        apply_curve = True
    elif rng is None or count < 4:
        x, y, z = generate_path(start, end, count, curve=curve)
    else:
        mid = (
            (start[0] + end[0]) / 2.0,
            (start[1] + end[1]) / 2.0,
            (start[2] + end[2]) / 2.0,
        )
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.hypot(dx, dy) or 1.0
        perp = (-dy / length, dx / length)
        swing = rng.uniform(-0.18, 0.18) * max(
            bounds[0][1] - bounds[0][0],
            bounds[1][1] - bounds[1][0],
        )
        mid = _clamp_point(
            (
                mid[0] + perp[0] * swing,
                mid[1] + perp[1] * swing,
                mid[2] + rng.uniform(-90.0, 90.0),
            ),
            bounds,
        )
        n1 = max(2, count // 2)
        n2 = max(2, count - n1 + 1)
        x1, y1, z1 = generate_path(start, mid, n1, curve=curve)
        x2, y2, z2 = generate_path(mid, end, n2, curve=curve)
        x = np.concatenate([x1[:-1], x2])
        y = np.concatenate([y1[:-1], y2])
        z = np.concatenate([z1[:-1], z2])

    if apply_curve and curve and count >= 2:
        t = np.linspace(0.0, 1.0, count, dtype=np.float64)
        if curve == "strafe_dive":
            z0 = float(start[2])
            z1 = float(end[2])
            z = z0 - (z0 - z1) * np.sin(t * math.pi / 2.0)
        elif curve == "escape_climb":
            z = z + 500.0 * np.sin(2.0 * math.pi * t)
        elif curve == "dogfight_maneuver":
            x = x + 400.0 * np.sin(2.0 * math.pi * t)
            y = y + 300.0 * np.sin(3.0 * math.pi * t)
            z = z + 200.0 * np.sin(2.0 * math.pi * t)

    x = np.clip(x, bounds[0][0], bounds[0][1])
    y = np.clip(y, bounds[1][0], bounds[1][1])
    z = np.clip(z, bounds[2][0], bounds[2][1])
    return x, y, z


def _smooth_series(
    series: NDArray[np.float64],
    *,
    passes: int = 2,
    alpha: float = 0.18,
) -> NDArray[np.float64]:
    if series.size < 3:
        return series
    out = series.copy()
    for _ in range(max(1, passes)):
        prev = out.copy()
        out[1:-1] = (1.0 - (2.0 * alpha)) * prev[1:-1] + alpha * (prev[:-2] + prev[2:])
    return out


def _variant_points(
    rng: random.Random | None,
    variant: str | None,
    target_xy: tuple[float, float] | None,
    secondary_xy: tuple[float, float] | None,
    start_pos: tuple[float, float, float] | None,
) -> tuple[
    tuple[float, float, float],
    tuple[float, float, float],
    tuple[float, float, float],
    tuple[float, float, float],
    tuple[float, float, float],
    tuple[float, float, float],
]:
    if rng is None:
        rng = random.Random()
    if variant is None:
        variant = rng.choice(
            ["classic", "wide_east", "tight_west", "high_alt", "low_alt", "north_arc", "south_arc"]
        )
    bounds = _scene_bounds()
    return _dynamic_points(
        rng,
        variant,
        bounds=bounds,
        target_xy=target_xy,
        secondary_xy=secondary_xy,
        start_pos=start_pos,
    )


def build_flight_plan_variant(
    phases: dict[str, Tuple[str, int]] | None = None,
    *,
    rng: random.Random | None,
    variant: str | None = None,
    target_xy: tuple[float, float] | None = None,
    secondary_xy: tuple[float, float] | None = None,
    start_pos: tuple[float, float, float] | None = None,
) -> tuple[
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
    Dict[str, Tuple[int, int]],
]:
    return build_flight_plan(
        phases,
        rng=rng,
        variant=variant,
        target_xy=target_xy,
        secondary_xy=secondary_xy,
        start_pos=start_pos,
    )

# ────────────────────────────────────────────────────────────────────────────
# 3 · High-level stitcher
# ────────────────────────────────────────────────────────────────────────────
def build_flight_plan(
    phases: dict[str, Tuple[str, int]] | None = None,
    *,
    rng: random.Random | None = None,
    variant: str | None = None,
    target_xy: tuple[float, float] | None = None,
    secondary_xy: tuple[float, float] | None = None,
    start_pos: tuple[float, float, float] | None = None,
) -> tuple[
    NDArray[np.float64],  # flight_x
    NDArray[np.float64],  # flight_y
    NDArray[np.float64],  # flight_z
    Dict[str, Tuple[int, int]],  # slice map
]:
    """Return *(x, y, z, slice_map)* for the full sortie."""
    if phases is None:
        phases = DEFAULT_PHASES
    phases = _normalize_phases(phases)

    bounds = _scene_bounds()
    if rng is None and variant is None and start_pos is None:
        a0, a1 = (0.0, 6000.0, 3000.0), (6000.0, 7500.0, 2200.0)
        b1, c1, d1, e1 = (
            (10000.0, 7000.0, 400.0),
            (15000.0, 7500.0, 650.0),
            (7000.0, 6000.0, 4000.0),
            (5000.0, 6500.0, 3500.0),
        )
    else:
        a0, a1, b1, c1, d1, e1 = _variant_points(
            rng,
            variant,
            target_xy,
            secondary_xy,
            start_pos,
        )

    points = [a0, a1, b1, c1, d1, e1]
    def _extrapolate(p1: tuple[float, float, float], p2: tuple[float, float, float]) -> tuple[float, float, float]:
        return (
            (2.0 * p1[0]) - p2[0],
            (2.0 * p1[1]) - p2[1],
            (2.0 * p1[2]) - p2[2],
        )

    # five main legs
    prev_a = _extrapolate(points[0], points[1])
    next_a = points[2]
    xA, yA, zA = _segment_points(
        a0,
        a1,
        phases["Approach"][1],
        rng=rng,
        bounds=bounds,
        prev=prev_a,
        next=next_a,
    )
    prev_b = points[0]
    next_b = points[3]
    xB, yB, zB = _segment_points(
        a1,
        b1,
        phases["Strafe"][1],
        curve="strafe_dive",
        rng=rng,
        bounds=bounds,
        prev=prev_b,
        next=next_b,
    )
    prev_c = points[1]
    next_c = points[4]
    xC, yC, zC = _segment_points(
        b1,
        c1,
        phases["Bombing"][1],
        rng=rng,
        bounds=bounds,
        prev=prev_c,
        next=next_c,
    )
    prev_d = points[2]
    next_d = points[5]
    xD, yD, zD = _segment_points(
        c1,
        d1,
        phases["Escape"][1],
        curve="escape_climb",
        rng=rng,
        bounds=bounds,
        prev=prev_d,
        next=next_d,
    )
    prev_e = points[3]
    next_e = _extrapolate(points[5], points[4])
    xE, yE, zE = _segment_points(
        d1,
        e1,
        phases["Dogfight"][1],
        curve="dogfight_maneuver",
        rng=rng,
        bounds=bounds,
        prev=prev_e,
        next=next_e,
    )

    # victory fly-bys
    span_xy = min(bounds[0][1] - bounds[0][0], bounds[1][1] - bounds[1][0])
    v_dx = max(1800.0, 0.08 * span_xy)
    v_dz = max(900.0, 0.03 * span_xy)
    v_mid = _clamp_point((e1[0] + v_dx, e1[1], e1[2] + v_dz), bounds)
    xV1, yV1, zV1 = _segment_points(
        e1, v_mid, 80, curve="escape_climb", rng=rng, bounds=bounds
    )
    xV2, yV2, zV2 = _segment_points(
        v_mid, a0, 120, curve="dogfight_maneuver", rng=rng, bounds=bounds
    )

    flight_x = np.concatenate([xA, xB, xC, xD, xE, xV1, xV2])
    flight_y = np.concatenate([yA, yB, yC, yD, yE, yV1, yV2])
    flight_z = np.concatenate([zA, zB, zC, zD, zE, zV1, zV2])

    flight_x = _smooth_series(flight_x, passes=2, alpha=0.18)
    flight_y = _smooth_series(flight_y, passes=2, alpha=0.18)
    flight_x = np.clip(flight_x, bounds[0][0], bounds[0][1])
    flight_y = np.clip(flight_y, bounds[1][0], bounds[1][1])

    slices: Dict[str, Tuple[int, int]] = {}
    idx = 0
    for name in _PHASE_ORDER:
        _, n = phases[name]
        slices[name] = (idx, idx + n)
        idx += n
    slices["Victory1"] = (idx, idx + len(xV1))
    idx += len(xV1)
    slices["Victory2"] = (idx, idx + len(xV2))

    return flight_x, flight_y, flight_z, slices

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence, Optional

import math


@dataclass(frozen=True)
class Dimensions:
    """Approximate dimensions used for procedural blueprints.

    All units are meters.

    Notes:
    - Not every platform has all dimensions available in your current dataset.
    - Any missing values should fall back to conservative defaults.
    """
    length_m: float
    width_m: float
    height_m: float

    # Aircraft-ish
    wingspan_m: Optional[float] = None

    # Ordnance-ish (missiles/bombs)
    diameter_m: Optional[float] = None


def _first_number(mapping: Mapping[str, Any], keys: Sequence[str]) -> Optional[float]:
    for k in keys:
        if k in mapping and mapping[k] is not None:
            try:
                v = float(mapping[k])
            except Exception:
                continue
            if math.isfinite(v) and v > 0.0:
                return v
    return None


def dims_from_mapping(spec: Mapping[str, Any], *, defaults: Dimensions) -> Dimensions:
    """Best-effort dimension extraction from a vehicle/weapon spec mapping.

    This intentionally tolerates schema drift. It tries a few common keys:
    - length_m, length, len_m, etc.
    - wingspan_m, wingspan, span_m, etc.
    - width_m, width, etc.
    - height_m, height, etc.
    - diameter_m, diameter, caliber, etc.

    If no value is found for a dimension, the corresponding default is used.

    Args:
        spec: Dict-like object (from DataStore or raw JSON).
        defaults: Fallback Dimensions (must be valid/positive).

    Returns:
        Dimensions with best-known values filled in.
    """
    length = _first_number(spec, (
        "length_m", "length", "len_m", "len", "overall_length_m",
        "Length", "Overall Length", "overall_length",
    )) or defaults.length_m

    width = _first_number(spec, (
        "width_m", "width", "overall_width_m",
        "Width", "Overall Width", "overall_width",
    )) or defaults.width_m

    height = _first_number(spec, (
        "height_m", "height", "overall_height_m",
        "Height", "Overall Height", "overall_height",
    )) or defaults.height_m

    wingspan = _first_number(spec, (
        "wingspan_m", "wingspan", "span_m", "span",
        "Wingspan", "Wing Span", "wing_span",
    ))
    if wingspan is None:
        wingspan = defaults.wingspan_m

    diameter = _first_number(spec, (
        "diameter_m", "diameter", "caliber_m", "calibre_m",
        "Diameter", "Caliber", "Calibre", "caliber",
    ))
    if diameter is None:
        diameter = defaults.diameter_m

    # Basic sanity clamp: you can still pass in weird data, but we won't emit NaNs.
    length = max(float(length), 0.1)
    width = max(float(width), 0.05)
    height = max(float(height), 0.05)
    if wingspan is not None:
        wingspan = max(float(wingspan), 0.1)
    if diameter is not None:
        diameter = max(float(diameter), 0.01)

    return Dimensions(
        length_m=length,
        width_m=width,
        height_m=height,
        wingspan_m=wingspan,
        diameter_m=diameter,
    )

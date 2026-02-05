"""Derive procedural blueprint parameters from vehicle/weapon specs.

These are *best-effort* helpers.

Reality:
- Your data sources will be messy.
- Not every vehicle will have a clean wingspan/length/height.

So this module focuses on:
  1) extracting what exists
  2) filling gaps with sane deterministic heuristics
  3) producing JSON-serializable parameter dicts

The procedural blueprint builders in `warbits.visual.procedural` do the final
geometry generation.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Mapping, MutableMapping, Tuple

Dims = dict[str, float | None]


def _get(spec: Mapping[str, Any], *keys: str, default: Any = None) -> Any:
    for k in keys:
        if k in spec and spec[k] is not None:
            return spec[k]
    return default


def _float_or_none(v: Any) -> float | None:
    try:
        if v is None:
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def _derive_dims_aircraft(spec: Mapping[str, Any]) -> Dims:
    # Prefer explicit meters fields if present.
    length = _float_or_none(_get(spec, "length_m", "length", "len_m"))
    wingspan = _float_or_none(_get(spec, "wingspan_m", "span_m", "wingspan"))
    height = _float_or_none(_get(spec, "height_m", "height"))

    # If we only know length, use a fighter-ish heuristic.
    if length is not None and wingspan is None:
        wingspan = 0.72 * length
    if length is not None and height is None:
        height = 0.20 * length

    # If we only know wingspan, infer length.
    if wingspan is not None and length is None:
        length = wingspan / 0.72
    if height is not None and length is None:
        length = height / 0.20

    # Clamp to sane lower bounds.
    if length is not None:
        length = max(1.0, length)
    if wingspan is not None:
        wingspan = max(0.8, wingspan)
    if height is not None:
        height = max(0.4, height)

    return {
        "length_m": length,
        "wingspan_m": wingspan,
        "height_m": height,
    }


def _derive_dims_ground(spec: Mapping[str, Any]) -> Dims:
    length = _float_or_none(_get(spec, "length_m", "length", "len_m"))
    width = _float_or_none(_get(spec, "width_m", "width"))
    height = _float_or_none(_get(spec, "height_m", "height"))

    # Basic MBT-ish heuristics.
    if length is not None and width is None:
        width = 0.32 * length
    if length is not None and height is None:
        height = 0.26 * length

    if width is not None and length is None:
        length = width / 0.32
    if height is not None and length is None:
        length = height / 0.26

    if length is not None:
        length = max(1.5, length)
    if width is not None:
        width = max(0.8, width)
    if height is not None:
        height = max(0.6, height)

    return {
        "length_m": length,
        "width_m": width,
        "height_m": height,
    }


def _derive_dims_missile(spec: Mapping[str, Any]) -> Dims:
    length = _float_or_none(_get(spec, "length_m", "length", "len_m"))
    diameter = _float_or_none(_get(spec, "diameter_m", "diameter"))

    # If diameter missing, guess ~1/25 of length.
    if length is not None and diameter is None:
        diameter = max(0.06, length / 25.0)

    if diameter is not None and length is None:
        length = diameter * 25.0

    if length is not None:
        length = max(0.25, length)
    if diameter is not None:
        diameter = max(0.04, diameter)

    return {
        "length_m": length,
        "diameter_m": diameter,
    }


def infer_domain(spec: Mapping[str, Any]) -> str:
    # Try explicit fields first.
    dom = _get(spec, "domain", "platform", "category")
    if isinstance(dom, str):
        d = dom.lower()
        if any(k in d for k in ("air", "plane", "jet", "fighter", "bomber", "helic")):
            return "air"
        if any(k in d for k in ("ground", "tank", "apc", "ifv", "spaa", "sam", "vehicle")):
            return "ground"
        if any(k in d for k in ("naval", "ship", "boat")):
            return "naval"
        if any(k in d for k in ("missile", "rocket", "bomb", "weapon", "gun")):
            return "ordnance"

    name = _get(spec, "name", "display_name", "id", default="")
    name_l = str(name).lower()
    if any(k in name_l for k in ("aim-", "agm-", "r-", "kh-", "mk ", "gbu", "fab", "s-", "hydra", "sidewinder")):
        return "ordnance"
    if any(k in name_l for k in ("t-", "m1", "abrams", "leopard", "bmp", "btr", "type 90", "challenger")):
        return "ground"
    if any(k in name_l for k in ("f-", "mig", "su-", "mirage", "tornado", "harrier", "phantom")):
        return "air"

    # Default assumption: vehicle.
    return "ground"


def infer_ordnance_kind(spec: Mapping[str, Any]) -> str:
    # Try explicit weapon_type
    wtype = _get(spec, "weapon_type", "type")
    if isinstance(wtype, str):
        t = wtype.lower()
        if "bomb" in t:
            return "bomb"
        if "rocket" in t:
            return "rocket"
        if "missile" in t:
            return "missile"

    name = str(_get(spec, "name", "id", default="")).lower()
    if any(k in name for k in ("gbu", "fab", "mk", "bomb")):
        return "bomb"
    if any(k in name for k in ("hydra", "s-", "rocket")):
        return "rocket"
    return "missile"


def derive_procedural_binding(spec: Mapping[str, Any]) -> Tuple[str, dict[str, Any]]:
    """Return (template_key, params_dict) for a procedural blueprint."""

    domain = infer_domain(spec)
    if domain == "air":
        # Defer to procedural aircraft params helper.
        from warbits.visual.procedural.aircraft import jet_params_from_spec

        dims = _derive_dims_aircraft(spec)
        defaults: MutableMapping[str, Any] = {
            "length_m": dims.get("length_m"),
            "wingspan_m": dims.get("wingspan_m"),
            "height_m": dims.get("height_m"),
        }
        params = jet_params_from_spec(spec, defaults=defaults)  # type: ignore[arg-type]
        return "proc:aircraft", asdict(params)

    if domain == "ground":
        from warbits.visual.procedural.ground import tank_params_from_spec

        dims = _derive_dims_ground(spec)
        defaults: MutableMapping[str, Any] = {
            "length_m": dims.get("length_m"),
            "width_m": dims.get("width_m"),
            "height_m": dims.get("height_m"),
        }
        params = tank_params_from_spec(spec, defaults=defaults)  # type: ignore[arg-type]
        return "proc:tank", asdict(params)

    if domain in ("ordnance", "weapon"):
        kind = infer_ordnance_kind(spec)
        dims = _derive_dims_missile(spec)
        if kind == "bomb":
            from warbits.visual.procedural.ordnance import \
                bomb_params_from_spec

            defaults: MutableMapping[str, Any] = {
                "length_m": dims.get("length_m"),
                "diameter_m": dims.get("diameter_m"),
            }
            params = bomb_params_from_spec(spec, defaults=defaults)  # type: ignore[arg-type]
            return "proc:bomb", asdict(params)

        if kind == "rocket":
            from warbits.visual.procedural.ordnance import \
                rocket_params_from_spec

            defaults: MutableMapping[str, Any] = {
                "length_m": dims.get("length_m"),
                "diameter_m": dims.get("diameter_m"),
            }
            params = rocket_params_from_spec(spec, defaults=defaults)  # type: ignore[arg-type]
            return "proc:rocket", asdict(params)

        from warbits.visual.procedural.ordnance import missile_params_from_spec

        defaults = {
            "length_m": dims.get("length_m"),
            "diameter_m": dims.get("diameter_m"),
        }
        params = missile_params_from_spec(spec, defaults=defaults)  # type: ignore[arg-type]
        return "proc:missile", asdict(params)

    # Fallback: treat as ground vehicle.
    from warbits.visual.procedural.ground import tank_params_from_spec

    dims = _derive_dims_ground(spec)
    defaults = {
        "length_m": dims.get("length_m"),
        "width_m": dims.get("width_m"),
        "height_m": dims.get("height_m"),
    }
    params = tank_params_from_spec(spec, defaults=defaults)  # type: ignore[arg-type]
    return "proc:tank", asdict(params)
    params = tank_params_from_spec(spec, defaults=defaults)  # type: ignore[arg-type]
    return "proc:tank", asdict(params)

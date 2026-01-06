from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class FieldSpec:
    name: str
    types: tuple[type, ...]
    required: bool = False
    allow_none: bool = False


@dataclass(frozen=True)
class TableSchema:
    name: str
    kind: str
    required_fields: tuple[FieldSpec, ...]
    optional_fields: tuple[FieldSpec, ...] = ()


def _f(
    name: str,
    *types: type,
    required: bool = False,
    allow_none: bool = False,
) -> FieldSpec:
    return FieldSpec(
        name=name,
        types=types,
        required=required,
        allow_none=allow_none,
    )


VEHICLE_SCHEMA = TableSchema(
    name="vehicles",
    kind="list",
    required_fields=(
        _f("id", str, required=True),
        _f("name", str, required=True),
        _f("vehicle_type", str, required=True),
        _f("sources", list, required=True),
    ),
    optional_fields=(
        _f("max_speed_mps", int, float),
        _f("best_climb_rate_mps", int, float),
        _f("best_climb_altitude_m", int, float),
    ),
)

WEAPON_SCHEMA = TableSchema(
    name="weapons",
    kind="list",
    required_fields=(
        _f("id", str, required=True),
        _f("name", str, required=True),
        _f("weapon_type", str, required=True),
        _f("warhead_id", str, required=True),
        _f("sources", list, required=True),
    ),
    optional_fields=(
        _f("max_speed_mps", int, float),
        _f("max_range_m", int, float),
        _f("min_range_m", int, float),
    ),
)

WARHEAD_SCHEMA = TableSchema(
    name="warheads",
    kind="list",
    required_fields=(
        _f("id", str, required=True),
        _f("weapon_id", str, required=True),
        _f("sources", list, required=True),
    ),
    optional_fields=(
        _f("warhead_type", str, allow_none=True),
        _f("explosive_mass_kg", int, float),
    ),
)

SENSOR_SCHEMA = TableSchema(
    name="sensors",
    kind="list",
    required_fields=(
        _f("id", str, required=True),
        _f("platform_name", str, required=True),
        _f("sources", list, required=True),
    ),
    optional_fields=(
        _f("name", str, allow_none=True),
        _f("sensor_type", str, allow_none=True),
        _f("role", str, allow_none=True),
    ),
)

TERRAIN_SCHEMA = TableSchema(
    name="terrain",
    kind="list",
    required_fields=(
        _f("id", str, required=True),
        _f("name", str, required=True),
        _f("biome", str, required=True),
    ),
    optional_fields=(
        _f("sources", list),
        _f("friction_coefficient", int, float),
        _f("roughness", int, float),
    ),
)

LOADOUTS_SCHEMA = TableSchema(
    name="loadouts",
    kind="dict",
    required_fields=(
        _f("hardpoints", list, required=True),
        _f("loadout_items", list, required=True),
        _f("loadouts", list, required=True),
        _f("sources", list, required=True),
    ),
)

SUMMARY_SCHEMA = TableSchema(
    name="summary",
    kind="dict",
    required_fields=(
        _f("counts", dict, required=True),
        _f("sources", dict, required=True),
        _f("warnings", list, required=True),
    ),
)

SCHEMAS: dict[str, TableSchema] = {
    "vehicles": VEHICLE_SCHEMA,
    "weapons": WEAPON_SCHEMA,
    "warheads": WARHEAD_SCHEMA,
    "sensors": SENSOR_SCHEMA,
    "terrain": TERRAIN_SCHEMA,
    "loadouts": LOADOUTS_SCHEMA,
    "summary": SUMMARY_SCHEMA,
}


def get_schema(name: str) -> TableSchema:
    return SCHEMAS[name]


def list_schema_names() -> list[str]:
    return sorted(SCHEMAS.keys())


def schema_fields(schema: TableSchema) -> Iterable[FieldSpec]:
    return (*schema.required_fields, *schema.optional_fields)


__all__ = [
    "FieldSpec",
    "TableSchema",
    "SCHEMAS",
    "get_schema",
    "list_schema_names",
    "schema_fields",
]

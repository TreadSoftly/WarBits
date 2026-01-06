"""
Data package for WarBits.

Place structured data files (json/csv/yaml) here so they can be packaged
alongside the code.
"""

from __future__ import annotations

import json
from importlib import resources
from typing import Any

TABLE_FILES = {
    "vehicles": "vehicles.json",
    "weapons": "weapons.json",
    "warheads": "warheads.json",
    "sensors": "sensors.json",
    "terrain": "terrain.json",
    "loadouts": "loadouts.json",
    "summary": "data_summary.json",
}


def list_tables() -> list[str]:
    return sorted(TABLE_FILES.keys())


def load_table(name: str) -> Any:
    if name not in TABLE_FILES:
        raise KeyError(f"Unknown table: {name}")
    table_file = TABLE_FILES[name]
    data_path = resources.files(__package__) / table_file
    with data_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)

from .store import DataStore, get_default_store # type: ignore[wrong-import-position]


__all__ = [
    "TABLE_FILES",
    "list_tables",
    "load_table",
    "DataStore",
    "get_default_store",
]

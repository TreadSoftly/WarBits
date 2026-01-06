from __future__ import annotations

from typing import Any

from .store import DataStore, get_default_store

VEHICLE_SPECS: dict[str, dict[str, Any]] = {}


def load_vehicle_specs(store: DataStore | None = None) -> dict[str, dict[str, Any]]:
    if VEHICLE_SPECS:
        return VEHICLE_SPECS
    store = store or get_default_store()
    specs: dict[str, dict[str, Any]] = {}
    for item in store.vehicles:
        item_id = item.get("id")
        if isinstance(item_id, str) and item_id:
            specs[item_id] = item
    VEHICLE_SPECS.update(specs)
    return VEHICLE_SPECS


__all__ = ["VEHICLE_SPECS", "load_vehicle_specs"]

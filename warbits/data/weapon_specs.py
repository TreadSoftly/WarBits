from __future__ import annotations

from typing import Any

from .store import DataStore, get_default_store

WEAPON_SPECS: dict[str, dict[str, Any]] = {}


def load_weapon_specs(store: DataStore | None = None) -> dict[str, dict[str, Any]]:
    if WEAPON_SPECS:
        return WEAPON_SPECS
    store = store or get_default_store()
    specs: dict[str, dict[str, Any]] = {}
    for item in store.weapons:
        item_id = item.get("id")
        if isinstance(item_id, str) and item_id:
            specs[item_id] = item
    WEAPON_SPECS.update(specs)
    return WEAPON_SPECS


__all__ = ["WEAPON_SPECS", "load_weapon_specs"]

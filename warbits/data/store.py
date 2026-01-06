from __future__ import annotations

import json
import re
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import TypeAlias, TypeGuard


JsonDict: TypeAlias = dict[str, object]
JsonList: TypeAlias = list[JsonDict]
TableData: TypeAlias = JsonList | JsonDict

TABLE_FILES: dict[str, str] = {
    "vehicles": "vehicles.json",
    "weapons": "weapons.json",
    "warheads": "warheads.json",
    "sensors": "sensors.json",
    "terrain": "terrain.json",
    "loadouts": "loadouts.json",
    "summary": "data_summary.json",
}


def _normalize_key(value: str) -> str:
    key = re.sub(r"[^a-z0-9]+", "_", value.strip().lower())
    return key.strip("_")


def _load_json(path: Path) -> TableData:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _is_dict(value: object) -> TypeGuard[JsonDict]:
    return isinstance(value, dict)


def _is_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def _as_list(data: object) -> JsonList:
    if not _is_list(data):
        return []
    items: JsonList = []
    for item in data:
        if _is_dict(item):
            items.append(item)
    return items


def _as_dict(data: object) -> JsonDict:
    if _is_dict(data):
        return data
    return {}


@dataclass
class DataStore:
    root: Path | None = None

    def __post_init__(self) -> None:
        if self.root is not None:
            self.root = Path(self.root)
        self._tables: dict[str, TableData] = {}
        self._index_cache: dict[str, dict[str, JsonDict]] = {}
        self._alias_cache: dict[str, dict[str, str]] = {}

    def list_tables(self) -> list[str]:
        return sorted(TABLE_FILES.keys())

    def load_table(self, name: str) -> TableData:
        if name not in TABLE_FILES:
            raise KeyError(f"Unknown table: {name}")
        if name in self._tables:
            return self._tables[name]
        if self.root is not None:
            path = self.root / TABLE_FILES[name]
            data = _load_json(path)
        else:
            data_path = resources.files("warbits.data") / TABLE_FILES[name]
            with data_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        self._tables[name] = data
        return data

    @classmethod
    def load_from_json_dir(cls, data_dir: str | Path) -> "DataStore":
        """Create a DataStore rooted at a JSON data directory."""
        return cls(root=Path(data_dir))

    @classmethod
    def from_json_dir(cls, data_dir: str | Path) -> "DataStore":
        """Back-compat alias for load_from_json_dir."""
        return cls.load_from_json_dir(data_dir)

    def _index(self, name: str) -> dict[str, JsonDict]:
        if name in self._index_cache:
            return self._index_cache[name]
        data: JsonList = _as_list(self.load_table(name))
        index: dict[str, JsonDict] = {}
        for item in data:
            item_id = item.get("id")
            if isinstance(item_id, str) and item_id:
                index[item_id] = item
        self._index_cache[name] = index
        return index

    def _aliases(self, name: str) -> dict[str, str]:
        if name in self._alias_cache:
            return self._alias_cache[name]
        data: JsonList = _as_list(self.load_table(name))
        aliases: dict[str, str] = {}
        for item in data:
            item_id = item.get("id")
            if not isinstance(item_id, str) or not item_id:
                continue
            aliases[_normalize_key(item_id)] = item_id
            for key in ("name", "platform_name", "weapon_tag", "biome"):
                value = item.get(key)
                if isinstance(value, str) and value.strip():
                    aliases.setdefault(_normalize_key(value), item_id)
        self._alias_cache[name] = aliases
        return aliases

    def resolve_id(self, name: str, key: str) -> str | None:
        if not key:
            return None
        index = self._index(name)
        if key in index:
            return key
        aliases = self._aliases(name)
        return aliases.get(_normalize_key(key))

    def get(self, name: str, key: str) -> JsonDict:
        item_id = self.resolve_id(name, key)
        if item_id is None:
            raise KeyError(f"{name} id not found: {key}")
        return self._index(name)[item_id]

    @property
    def vehicles(self) -> JsonList:
        return _as_list(self.load_table("vehicles"))

    @property
    def weapons(self) -> JsonList:
        return _as_list(self.load_table("weapons"))

    @property
    def warheads(self) -> JsonList:
        return _as_list(self.load_table("warheads"))

    @property
    def sensors(self) -> JsonList:
        return _as_list(self.load_table("sensors"))

    @property
    def terrain(self) -> JsonList:
        return _as_list(self.load_table("terrain"))

    @property
    def loadouts(self) -> JsonDict:
        return _as_dict(self.load_table("loadouts"))

    @property
    def summary(self) -> JsonDict:
        return _as_dict(self.load_table("summary"))


_default_store: DataStore | None = None


def get_default_store() -> DataStore:
    global _default_store
    if _default_store is None:
        _default_store = DataStore()
    return _default_store


__all__ = [
    "DataStore",
    "TABLE_FILES",
    "get_default_store",
]

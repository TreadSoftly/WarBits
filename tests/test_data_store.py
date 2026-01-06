import unittest
from pathlib import Path

from warbits.data.store import DataStore


class TestDataStore(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parent / "fixtures" / "data"

    def test_resolve_vehicle_alias(self) -> None:
        store = DataStore(root=self.root)
        resolved = store.resolve_id("vehicles", "Test Plane")
        self.assertEqual(resolved, "test_plane")

    def test_get_weapon_by_alias(self) -> None:
        store = DataStore(root=self.root)
        weapon = store.get("weapons", "Test Missile")
        self.assertEqual(weapon["id"], "test_missile")

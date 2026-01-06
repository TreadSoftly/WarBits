import unittest
from pathlib import Path

from warbits.data.store import DataStore
from warbits.data.validate import validate_all


class TestDataValidation(unittest.TestCase):
    def test_fixture_data_validates(self) -> None:
        root = Path(__file__).resolve().parent / "fixtures" / "data"
        store = DataStore(root=root)
        report = validate_all(store)
        self.assertEqual(report.error_count, 0)
        self.assertEqual(report.warning_count, 0)

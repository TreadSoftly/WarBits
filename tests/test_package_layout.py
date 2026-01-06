import importlib
import unittest


class TestPackageLayout(unittest.TestCase):
    def test_archive_packages_not_importable(self) -> None:
        with self.assertRaises(ImportError):
            importlib.import_module("warbits.lib")

    def test_simlib_runtime_imports(self) -> None:
        importlib.import_module("warbits.simlib.ai")
        importlib.import_module("warbits.simlib.mission")

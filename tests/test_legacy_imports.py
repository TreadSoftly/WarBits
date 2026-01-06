import os
import unittest

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("WARBITS_FULLSCREEN", "0")


class TestLegacyImports(unittest.TestCase):
    def test_legacy_modules_import(self) -> None:
        __import__("warbits.data.phases")
        __import__("warbits.data.vehicle_specs")
        __import__("warbits.data.weapon_specs")
        __import__("warbits.logic.ai")
        __import__("warbits.scene.effects")
        __import__("warbits.scene.models")
        __import__("warbits.scene.mpl_setup")
        __import__("warbits.utils.hardware")
        __import__("warbits.physics.ballistics_fast")

import unittest
from typing import Dict

import numpy as np

from warbits.simlib.mission.triggers import EnterZoneTrigger, TimeTrigger
from warbits.simlib.mission.types import EntitySnapshot, Pose, WorldSnapshot


class DummyWorld:
    def __init__(self):
        self._time = 0.0
        self.entities = {
            "p1": EntitySnapshot("p1", "blue", True, Pose.from_arrays([0, 0, 0], [0, 0, 0])),
        }

    def snapshot(self):
        return WorldSnapshot(time_s=self._time, entities=tuple(self.entities.values()))

    def set_time(self, time_s: float) -> None:
        self._time = float(time_s)

    def is_alive(self, entity_id: str) -> bool:
        return bool(self.entities[entity_id].alive)

    def get_pose(self, entity_id: str) -> Pose:
        return self.entities[entity_id].pose


class TestTriggers(unittest.TestCase):
    def test_time_trigger(self):
        w = DummyWorld()
        t = TimeTrigger(id="t", fire_time_s=5.0)
        flags: Dict[str, object] = {}
        out0 = t.tick(w, [], flags)
        self.assertEqual(out0, [])
        w.set_time(5.0)
        out1 = t.tick(w, [], flags)
        self.assertTrue(len(out1) >= 1)
        # shouldn't fire again (non-repeatable)
        out2 = t.tick(w, [], flags)
        self.assertEqual(out2, [])

    def test_enter_zone_trigger(self):
        w = DummyWorld()
        tz = EnterZoneTrigger(id="z", entity_id="p1", center_m=np.array([100.0, 0.0, 0.0]), radius_m=10.0)
        flags: Dict[str, object] = {}
        out0 = tz.tick(w, [], flags)
        self.assertEqual(out0, [])
        w.entities["p1"] = EntitySnapshot("p1", "blue", True, Pose.from_arrays([100, 0, 0], [0, 0, 0]))
        out1 = tz.tick(w, [], flags)
        self.assertTrue(len(out1) >= 1)


if __name__ == "__main__":
    unittest.main()
    unittest.main()

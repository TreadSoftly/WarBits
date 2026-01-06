import unittest
import numpy as np

from warbits.simlib.mission.objectives import DestroyEntitiesObjective, ObjectiveStatus, ReachZoneObjective
from warbits.simlib.mission.types import Pose, EntitySnapshot, WorldSnapshot


class DummyWorld:
    def __init__(self):
        self._time = 0.0
        self.entities = {
            "t1": EntitySnapshot("t1", "red", True, Pose.from_arrays([0,0,0],[0,0,0])),
            "t2": EntitySnapshot("t2", "red", True, Pose.from_arrays([0,0,0],[0,0,0])),
            "p1": EntitySnapshot("p1", "blue", True, Pose.from_arrays([0,0,0],[0,0,0])),
        }

    def snapshot(self):
        return WorldSnapshot(time_s=self._time, entities=tuple(self.entities.values()))

    def is_alive(self, entity_id: str) -> bool:
        return bool(self.entities[entity_id].alive)

    def get_pose(self, entity_id: str) -> Pose:
        return self.entities[entity_id].pose


class TestObjectives(unittest.TestCase):
    def test_destroy_objective(self):
        w = DummyWorld()
        obj = DestroyEntitiesObjective(id="o1", title="Destroy", targets=("t1","t2"))
        obj.activate()
        self.assertEqual(obj.status, ObjectiveStatus.ACTIVE)

        # still alive => active
        obj.update(w, [])
        self.assertEqual(obj.status, ObjectiveStatus.ACTIVE)

        # kill them
        w.entities["t1"] = EntitySnapshot("t1", "red", False, w.entities["t1"].pose)
        w.entities["t2"] = EntitySnapshot("t2", "red", False, w.entities["t2"].pose)
        obj.update(w, [])
        self.assertEqual(obj.status, ObjectiveStatus.SUCCESS)

    def test_reach_zone(self):
        w = DummyWorld()
        center = np.array([100.0, 0.0, 0.0])
        obj = ReachZoneObjective(id="rz", title="Reach", entity_id="p1", center_m=center, radius_m=50.0)
        obj.activate()
        self.assertEqual(obj.status, ObjectiveStatus.ACTIVE)

        # not there yet
        obj.update(w, [])
        self.assertEqual(obj.status, ObjectiveStatus.ACTIVE)

        # move into zone
        w.entities["p1"] = EntitySnapshot("p1", "blue", True, Pose.from_arrays([110,0,0],[0,0,0]))
        obj.update(w, [])
        self.assertEqual(obj.status, ObjectiveStatus.SUCCESS)


if __name__ == "__main__":
    unittest.main()

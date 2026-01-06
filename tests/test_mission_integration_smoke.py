import unittest

from warbits.core.sim import Simulation
from warbits.logic.mission_runtime import DEFAULT_TIME_LIMIT_S
from warbits.simlib.mission.objectives import ObjectiveStatus


class TestMissionIntegrationSmoke(unittest.TestCase):
    def test_time_limit_mission_deterministic(self) -> None:
        sim = Simulation(seed=1234)
        frames = int((DEFAULT_TIME_LIMIT_S / sim.services.clock.dt_s) + 5)
        for _ in range(frames):
            sim.step()
        result = sim.mission_result
        self.assertIsNotNone(result)
        assert result is not None
        statuses = list(result.objective_status.values())
        self.assertTrue(statuses)
        self.assertIn(ObjectiveStatus.SUCCESS, statuses)

        sim2 = Simulation(seed=1234)
        for _ in range(frames):
            sim2.step()
        result2 = sim2.mission_result
        self.assertIsNotNone(result2)
        assert result2 is not None
        self.assertEqual(result.objective_status, result2.objective_status)


if __name__ == "__main__":
    unittest.main()

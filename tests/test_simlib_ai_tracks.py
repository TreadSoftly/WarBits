import unittest
import numpy as np

from warbits.simlib.ai import DeterministicRNG
from warbits.simlib.ai.tracks import Observation, TrackManager


class TestTrackManager(unittest.TestCase):
    def test_track_creation_and_update(self):
        tm = TrackManager(rng=DeterministicRNG(42), gate_m=1000.0)
        obs1 = Observation(time_s=0.0, sensor_id="radar", pos_m=np.array([0.0, 0.0, 0.0]))
        tid1 = tm.ingest(obs1)
        self.assertTrue(tid1.startswith("trk-"))
        self.assertEqual(len(tm.tracks()), 1)

        # nearby update should match same track
        obs2 = Observation(time_s=0.1, sensor_id="radar", pos_m=np.array([10.0, 0.0, 0.0]))
        tid2 = tm.ingest(obs2)
        self.assertEqual(tid1, tid2)
        self.assertEqual(len(tm.tracks()), 1)

        # far away -> new track
        obs3 = Observation(time_s=0.2, sensor_id="radar", pos_m=np.array([5000.0, 0.0, 0.0]))
        tid3 = tm.ingest(obs3)
        self.assertNotEqual(tid1, tid3)
        self.assertEqual(len(tm.tracks()), 2)


if __name__ == "__main__":
    unittest.main()

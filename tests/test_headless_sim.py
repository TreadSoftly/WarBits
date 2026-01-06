import unittest

from warbits.core.sim import Simulation


class TestHeadlessSim(unittest.TestCase):
    def test_runs_headless(self) -> None:
        sim = Simulation(seed=1234)
        for _ in range(100):
            sim.step()

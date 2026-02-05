import unittest

from warbits.simlib.ai import DeterministicRNG
from warbits.simlib.ai.goap import GoapAction, GoapPlanner


class TestGoap(unittest.TestCase):
    def test_plan_basic(self):
        rng = DeterministicRNG(123)
        actions = [
            GoapAction("get_weapon", 1.0, pre={"armed": False}, eff={"armed": True}),
            GoapAction("find_target", 1.0, pre={"has_target": False}, eff={"has_target": True}),
            GoapAction("engage", 2.0, pre={"armed": True, "has_target": True}, eff={"engaging": True}),
        ]
        planner = GoapPlanner(actions=actions, rng=rng)
        start = frozenset({"armed": False, "has_target": False, "engaging": False}.items())
        goal = {"engaging": True}
        plan = planner.plan(start, goal)
        self.assertIsNotNone(plan)
        assert plan is not None
        self.assertEqual([a.name for a in plan], ["get_weapon", "find_target", "engage"])


if __name__ == "__main__":
    unittest.main()

import unittest

from warbits.simlib.ai import AIContext, Blackboard, DeterministicRNG
from warbits.simlib.ai.utility import UtilityAction, UtilityPolicy


class TestUtilityPolicy(unittest.TestCase):
    def test_argmax_choice(self):
        bb = Blackboard()
        ctx = AIContext(rng=DeterministicRNG(10), bb=bb, now_s=0.0, dt_s=0.1)

        def s1(ctx: AIContext):
            return 0.2

        def s2(ctx: AIContext):
            return 0.9

        def a1(ctx: AIContext):
            ctx.bb.set("picked", "a1")

        def a2(ctx: AIContext):
            ctx.bb.set("picked", "a2")

        policy = UtilityPolicy(
            actions=[
                UtilityAction("a1", s1, a1),
                UtilityAction("a2", s2, a2),
            ]
        )
        name = policy.tick(ctx)
        self.assertEqual(name, "a2")
        self.assertEqual(bb.get("picked"), "a2")

    def test_hysteresis_keeps_last(self):
        bb = Blackboard()
        bb.set("utility.last_action", "hold")
        ctx = AIContext(rng=DeterministicRNG(11), bb=bb, now_s=0.0, dt_s=0.1)

        def s_hold(ctx: AIContext):
            return 0.90

        def s_switch(ctx: AIContext):
            return 0.92  # only slightly better

        def a_hold(ctx: AIContext):
            ctx.bb.set("picked", "hold")

        def a_switch(ctx: AIContext):
            ctx.bb.set("picked", "switch")

        policy = UtilityPolicy(
            actions=[
                UtilityAction("hold", s_hold, a_hold),
                UtilityAction("switch", s_switch, a_switch),
            ],
            hysteresis_margin=0.05,
        )

        name = policy.tick(ctx)
        self.assertEqual(name, "hold")
        self.assertEqual(bb.get("picked"), "hold")


if __name__ == "__main__":
    unittest.main()

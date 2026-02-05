import unittest

from warbits.simlib.ai import (
    Action,
    AIContext,
    BehaviorTree,
    Blackboard,
    Cooldown,
    DeterministicRNG,
    Selector,
    Sequence,
    Status,
)


class TestBehaviorTree(unittest.TestCase):
    def test_sequence_success(self):
        bb = Blackboard()
        ctx = AIContext(rng=DeterministicRNG(1), bb=bb, now_s=0.0, dt_s=0.1)

        def set_a(ctx: AIContext):
            ctx.bb.set("a", True)
            return Status.SUCCESS

        def set_b(ctx: AIContext):
            ctx.bb.set("b", True)
            return Status.SUCCESS

        tree = BehaviorTree(Sequence([Action(set_a, "set_a"), Action(set_b, "set_b")]))
        st = tree.tick(ctx)
        self.assertEqual(st, Status.SUCCESS)
        self.assertTrue(bb.get("a"))
        self.assertTrue(bb.get("b"))

    def test_selector_fallback(self):
        bb = Blackboard()
        ctx = AIContext(rng=DeterministicRNG(2), bb=bb, now_s=0.0, dt_s=0.1)

        def fail(ctx: AIContext):
            return Status.FAILURE

        def succeed(ctx: AIContext):
            ctx.bb.set("ok", 1)
            return Status.SUCCESS

        tree = BehaviorTree(Selector([Action(fail, "fail"), Action(succeed, "succeed")]))
        st = tree.tick(ctx)
        self.assertEqual(st, Status.SUCCESS)
        self.assertEqual(bb.get("ok"), 1)

    def test_cooldown_blocks_spam(self):
        bb = Blackboard()
        ctx = AIContext(rng=DeterministicRNG(3), bb=bb, now_s=0.0, dt_s=0.1)

        def fire(ctx: AIContext):
            ctx.bb.set("fires", int(ctx.bb.get("fires", 0)) + 1)
            return Status.SUCCESS

        node = Cooldown(Action(fire, "fire"), cooldown_s=1.0, id="gun")
        tree = BehaviorTree(node)

        # t=0 success
        st0 = tree.tick(ctx)
        self.assertEqual(st0, Status.SUCCESS)

        # t=0.5 blocked
        ctx.now_s = 0.5
        st1 = tree.tick(ctx)
        self.assertEqual(st1, Status.FAILURE)

        # t=1.0 allowed again
        ctx.now_s = 1.0
        st2 = tree.tick(ctx)
        self.assertEqual(st2, Status.SUCCESS)

        self.assertEqual(bb.get("fires"), 2)


if __name__ == "__main__":
    unittest.main()

import random
import unittest

from warbits.logic.scenario import (
    ActionSchedule,
    BulletWindow,
    DecisionConfig,
    DecisionDirector,
    build_action_schedule,
)


class TestScenario(unittest.TestCase):
    def test_schedule_deterministic(self) -> None:
        slice_map = {
            "Strafe": (10, 50),
            "Bombing": (60, 90),
            "Escape": (90, 120),
            "Dogfight": (120, 160),
        }
        rng1 = random.Random(42)
        rng2 = random.Random(42)
        schedule1 = build_action_schedule(slice_map, rng1, seed=42)
        schedule2 = build_action_schedule(slice_map, rng2, seed=42)
        self.assertEqual(schedule1, schedule2)

    def test_schedule_bounds(self) -> None:
        slice_map = {
            "Strafe": (10, 50),
            "Bombing": (60, 90),
            "Escape": (90, 120),
            "Dogfight": (120, 160),
        }
        rng = random.Random(7)
        schedule = build_action_schedule(slice_map, rng, seed=7)
        for window in schedule.bullet_windows:
            self.assertLess(window.start, window.end)
            self.assertGreaterEqual(window.start, 10)
            self.assertLessEqual(window.end, 160)
        if schedule.bomb_frame is not None:
            self.assertGreaterEqual(schedule.bomb_frame, 60)
            self.assertLess(schedule.bomb_frame, 90)
        if schedule.bogie_appear_frame is not None:
            self.assertGreaterEqual(schedule.bogie_appear_frame, 90)
            self.assertLess(schedule.bogie_appear_frame, 120)
        if schedule.bogie_hit_frame is not None:
            self.assertGreaterEqual(schedule.bogie_hit_frame, 120)
            self.assertLess(schedule.bogie_hit_frame, 160)

    def test_bullet_window_allows(self) -> None:
        window = BulletWindow(start=10, end=20, every=3, offset=0)
        self.assertTrue(window.allows(10))
        self.assertFalse(window.allows(11))
        self.assertTrue(window.allows(13))
        self.assertFalse(window.allows(20))

    def test_action_schedule_should_fire(self) -> None:
        schedule = ActionSchedule(
            bullet_windows=[BulletWindow(10, 15, every=2, offset=0)],
            rocket_frames=[],
            bomb_frame=None,
            bogie_appear_frame=None,
            bogie_hit_frame=None,
            bogie_closing_factor=0.2,
            seed=1,
        )
        self.assertTrue(schedule.should_fire_bullets(10))
        self.assertFalse(schedule.should_fire_bullets(11))
        self.assertTrue(schedule.should_fire_bullets(12))

    def test_decision_deterministic(self) -> None:
        slice_map = {
            "Approach": (0, 10),
            "Strafe": (10, 40),
            "Bombing": (40, 60),
            "Escape": (60, 80),
            "Dogfight": (80, 120),
        }
        config = DecisionConfig(
            decision_interval=1,
            hold_weight=0.0,
            ammo_bursts=20,
            ammo_rockets=4,
            ammo_bombs=1,
        )
        director_a = DecisionDirector(seed=77, config=config)
        director_b = DecisionDirector(seed=77, config=config)
        state_a = director_a.reset(slice_map)
        state_b = director_b.reset(slice_map)
        actions_a = [director_a.step(frame, state_a) for frame in range(0, 60)]
        actions_b = [director_b.step(frame, state_b) for frame in range(0, 60)]
        self.assertEqual(actions_a, actions_b)

    def test_decision_phase_gates(self) -> None:
        slice_map = {
            "Approach": (0, 10),
            "Strafe": (10, 40),
            "Bombing": (40, 60),
            "Escape": (60, 80),
            "Dogfight": (80, 120),
        }
        config = DecisionConfig(
            decision_interval=1,
            hold_weight=0.0,
            ammo_bursts=20,
            ammo_rockets=4,
            ammo_bombs=1,
        )
        director = DecisionDirector(seed=91, config=config)
        state = director.reset(slice_map)
        for frame in range(0, 90):
            result = director.step(frame, state)
            phase = state.phase_table[frame]
            if result.drop_bomb:
                self.assertEqual(phase, "Bombing")
            if result.launch_rocket:
                self.assertIn(phase, {"Strafe", "Bombing", "Dogfight"})
            if result.fire_bullets:
                self.assertIn(phase, {"Strafe", "Dogfight"})

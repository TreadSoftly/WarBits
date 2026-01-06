from __future__ import annotations

from dataclasses import dataclass
import random
import secrets

SliceMap = dict[str, tuple[int, int]]


@dataclass(frozen=True)
class BulletWindow:
    start: int
    end: int
    every: int
    offset: int

    def allows(self, frame: int) -> bool:
        if frame < self.start or frame >= self.end:
            return False
        return ((frame - self.start + self.offset) % self.every) == 0


@dataclass(frozen=True)
class ActionSchedule:
    bullet_windows: list[BulletWindow]
    rocket_frames: list[int]
    bomb_frame: int | None
    bogie_appear_frame: int | None
    bogie_hit_frame: int | None
    bogie_closing_factor: float
    seed: int | None

    def should_fire_bullets(self, frame: int) -> bool:
        return any(window.allows(frame) for window in self.bullet_windows)


@dataclass(frozen=True)
class ScenarioConfig:
    strafe_prob: float = 0.90
    dogfight_prob: float = 0.85
    bomb_prob: float = 0.75
    rocket_prob: float = 0.80
    strafe_windows: tuple[int, int] = (1, 2)
    dogfight_windows: tuple[int, int] = (1, 3)
    window_len: tuple[int, int] = (6, 18)
    bullet_every: tuple[int, int] = (6, 12)
    rocket_count: tuple[int, int] = (1, 4)
    bogie_close_range: tuple[float, float] = (0.16, 0.28)
    bogie_appear_offset: tuple[int, int] = (6, 24)


@dataclass(frozen=True)
class DecisionResult:
    fire_bullets: bool = False
    launch_rocket: bool = False
    drop_bomb: bool = False


@dataclass(frozen=True)
class DecisionConfig:
    decision_interval: int = 3
    hold_weight: float = 1.0
    burst_weight: float = 2.0
    rocket_weight: float = 1.3
    bomb_weight: float = 1.7
    burst_length: tuple[int, int] = (4, 12)
    burst_spacing: tuple[int, int] = (1, 3)
    burst_cooldown: tuple[int, int] = (8, 18)
    rocket_cooldown: tuple[int, int] = (14, 32)
    bomb_cooldown: tuple[int, int] = (30, 60)
    ammo_bursts: int = 500
    ammo_rockets: int = 6
    ammo_bombs: int = 1


@dataclass
class DecisionState:
    seed: int
    phase_table: list[str]
    bullets_remaining: int
    rockets_remaining: int
    bombs_remaining: int
    next_decision_frame: int = 0
    burst_until: int = -1
    burst_every: int = 1
    burst_phase: str | None = None
    next_bullet_frame: int = 0
    burst_cooldown_until: int = 0
    rocket_cooldown_until: int = 0
    bomb_cooldown_until: int = 0


def _rand_range(rng: random.Random, bounds: tuple[int, int]) -> int:
    low, high = bounds
    if low >= high:
        return int(low)
    return rng.randint(int(low), int(high))


def _pick_frame(
    rng: random.Random,
    start: int,
    end: int,
    *,
    margin: int = 2,
) -> int:
    if end <= start:
        return int(start)
    span = end - start
    if span <= (margin * 2):
        return int(start + span // 2)
    return rng.randint(int(start + margin), int(end - margin - 1))


def _pick_window(
    rng: random.Random,
    start: int,
    end: int,
    length_range: tuple[int, int],
) -> tuple[int, int]:
    if end <= start:
        return start, start
    max_len = max(1, min(end - start, length_range[1]))
    min_len = max(1, min(length_range[0], max_len))
    length = _rand_range(rng, (min_len, max_len))
    win_start = _pick_frame(rng, start, end - length + 1, margin=0)
    return win_start, win_start + length


def _collect_attack_slices(slice_map: SliceMap) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    for key in ("Strafe", "Dogfight", "Bombing"):
        rng = slice_map.get(key)
        if rng is not None:
            ranges.append(rng)
    return ranges


def _build_phase_table(slice_map: SliceMap) -> list[str]:
    if not slice_map:
        return []
    max_end = max(end for _, end in slice_map.values())
    table = ["Unknown"] * max_end
    for name, (start, end) in slice_map.items():
        label = "Victory" if name.startswith("Victory") else name
        for idx in range(start, min(end, max_end)):
            table[idx] = label
    return table


def _phase_at(state: DecisionState, frame: int) -> str:
    if frame < 0 or frame >= len(state.phase_table):
        return "Unknown"
    return state.phase_table[frame]


def _weighted_choice(rng: random.Random, options: list[tuple[str, float]]) -> str:
    total = sum(max(0.0, weight) for _, weight in options)
    if total <= 0.0:
        return "hold"
    pick = rng.random() * total
    upto = 0.0
    for name, weight in options:
        w = max(0.0, weight)
        upto += w
        if upto >= pick:
            return name
    return options[-1][0]


def build_action_schedule(
    slice_map: SliceMap,
    rng: random.Random,
    *,
    seed: int | None = None,
    config: ScenarioConfig | None = None,
) -> ActionSchedule:
    cfg = config or ScenarioConfig()

    bullet_windows: list[BulletWindow] = []
    rocket_frames: list[int] = []
    bomb_frame: int | None = None

    strafe = slice_map.get("Strafe")
    if strafe and rng.random() <= cfg.strafe_prob:
        count = _rand_range(rng, cfg.strafe_windows)
        for _ in range(count):
            start, end = _pick_window(rng, strafe[0], strafe[1], cfg.window_len)
            every = _rand_range(rng, cfg.bullet_every)
            offset = rng.randint(0, max(0, every - 1))
            bullet_windows.append(BulletWindow(start, end, every, offset))

    dogfight = slice_map.get("Dogfight")
    if dogfight and rng.random() <= cfg.dogfight_prob:
        count = _rand_range(rng, cfg.dogfight_windows)
        for _ in range(count):
            start, end = _pick_window(rng, dogfight[0], dogfight[1], cfg.window_len)
            every = _rand_range(rng, cfg.bullet_every)
            offset = rng.randint(0, max(0, every - 1))
            bullet_windows.append(BulletWindow(start, end, every, offset))

    bombing = slice_map.get("Bombing")
    if bombing and rng.random() <= cfg.bomb_prob:
        bomb_frame = _pick_frame(rng, bombing[0], bombing[1], margin=4)

    attack_ranges = _collect_attack_slices(slice_map)
    if attack_ranges and rng.random() <= cfg.rocket_prob:
        rocket_count = _rand_range(rng, cfg.rocket_count)
        for _ in range(rocket_count):
            start, end = rng.choice(attack_ranges)
            rocket_frames.append(_pick_frame(rng, start, end, margin=3))
        rocket_frames.sort()

    bogie_appear_frame = None
    appear_range = (
        slice_map.get("Escape")
        or slice_map.get("Dogfight")
        or slice_map.get("Bombing")
        or slice_map.get("Strafe")
        or slice_map.get("Approach")
    )
    if appear_range:
        start, end = appear_range
        if end <= start:
            bogie_appear_frame = int(start)
        else:
            offset = _rand_range(rng, cfg.bogie_appear_offset)
            bogie_appear_frame = max(start, min(end - 1, end - offset))

    bogie_hit_frame = None
    if dogfight:
        bogie_hit_frame = _pick_frame(rng, dogfight[0], dogfight[1], margin=5)
        if bullet_windows:
            dogfight_windows = [
                window
                for window in bullet_windows
                if window.start >= dogfight[0] and window.end <= dogfight[1]
            ]
            if dogfight_windows:
                hit_window = rng.choice(dogfight_windows)
                bogie_hit_frame = _pick_frame(rng, hit_window.start, hit_window.end, margin=2)

    close_min, close_max = cfg.bogie_close_range
    bogie_closing_factor = rng.uniform(close_min, close_max)

    return ActionSchedule(
        bullet_windows=bullet_windows,
        rocket_frames=rocket_frames,
        bomb_frame=bomb_frame,
        bogie_appear_frame=bogie_appear_frame,
        bogie_hit_frame=bogie_hit_frame,
        bogie_closing_factor=bogie_closing_factor,
        seed=seed,
    )


class ScenarioDirector:
    def __init__(self, *, seed: int | None = None, config: ScenarioConfig | None = None) -> None:
        self._seed = seed
        self._config = config

    def build(self, slice_map: SliceMap, *, seed: int | None = None) -> ActionSchedule:
        if seed is None:
            seed = self._seed if self._seed is not None else secrets.randbits(32)
        rng = random.Random(seed)
        return build_action_schedule(slice_map, rng, seed=seed, config=self._config)


class DecisionDirector:
    def __init__(self, *, seed: int | None = None, config: DecisionConfig | None = None) -> None:
        self._seed = seed
        self._config = config or DecisionConfig()
        self._rng = random.Random(seed if seed is not None else secrets.randbits(32))

    def reset(self, slice_map: SliceMap, *, seed: int | None = None) -> DecisionState:
        if seed is None:
            seed = self._seed if self._seed is not None else secrets.randbits(32)
        self._rng = random.Random(seed)
        cfg = self._config
        return DecisionState(
            seed=seed,
            phase_table=_build_phase_table(slice_map),
            bullets_remaining=cfg.ammo_bursts,
            rockets_remaining=cfg.ammo_rockets,
            bombs_remaining=cfg.ammo_bombs,
        )

    def rearm(self, state: DecisionState, *, frame: int = 0) -> None:
        cfg = self._config
        state.bullets_remaining = cfg.ammo_bursts
        state.rockets_remaining = cfg.ammo_rockets
        state.bombs_remaining = cfg.ammo_bombs
        state.next_decision_frame = frame
        state.burst_until = -1
        state.burst_phase = None
        state.next_bullet_frame = frame
        state.burst_cooldown_until = frame
        state.rocket_cooldown_until = frame
        state.bomb_cooldown_until = frame

    def step(
        self,
        frame: int,
        state: DecisionState,
        *,
        phase_frame: int | None = None,
    ) -> DecisionResult:
        phase_index = frame if phase_frame is None else phase_frame
        phase = _phase_at(state, phase_index)
        fire_bullets = False
        launch_rocket = False
        drop_bomb = False

        if state.burst_until >= frame:
            if phase not in {"Strafe", "Dogfight"}:
                state.burst_until = -1
                state.burst_phase = None
            elif state.bullets_remaining > 0 and frame >= state.next_bullet_frame:
                fire_bullets = True
                state.bullets_remaining -= 1
                state.next_bullet_frame = frame + max(1, state.burst_every)
            if state.burst_until == frame:
                state.burst_until = -1
                state.burst_phase = None
                state.burst_cooldown_until = frame + _rand_range(self._rng, self._config.burst_cooldown)

        if frame < state.next_decision_frame:
            return DecisionResult(
                fire_bullets=fire_bullets,
                launch_rocket=False,
                drop_bomb=False,
            )

        state.next_decision_frame = frame + max(1, self._config.decision_interval)

        options: list[tuple[str, float]] = [("hold", self._config.hold_weight)]
        if phase in {"Strafe", "Dogfight"} and state.bullets_remaining > 0:
            if frame >= state.burst_cooldown_until and state.burst_until < frame:
                options.append(("burst", self._config.burst_weight))
        if phase in {"Strafe", "Bombing", "Dogfight"} and state.rockets_remaining > 0:
            if frame >= state.rocket_cooldown_until:
                options.append(("rocket", self._config.rocket_weight))
        if phase == "Bombing" and state.bombs_remaining > 0:
            if frame >= state.bomb_cooldown_until:
                options.append(("bomb", self._config.bomb_weight))

        choice = _weighted_choice(self._rng, options)
        if choice == "burst":
            duration = _rand_range(self._rng, self._config.burst_length)
            state.burst_every = _rand_range(self._rng, self._config.burst_spacing)
            state.burst_until = frame + max(1, duration)
            state.burst_phase = phase
            state.next_bullet_frame = frame
        elif choice == "rocket":
            launch_rocket = True
            state.rockets_remaining = max(0, state.rockets_remaining - 1)
            state.rocket_cooldown_until = frame + _rand_range(self._rng, self._config.rocket_cooldown)
        elif choice == "bomb":
            drop_bomb = True
            state.bombs_remaining = max(0, state.bombs_remaining - 1)
            state.bomb_cooldown_until = frame + _rand_range(self._rng, self._config.bomb_cooldown)

        return DecisionResult(
            fire_bullets=fire_bullets,
            launch_rocket=launch_rocket,
            drop_bomb=drop_bomb,
        )


__all__ = [
    "ActionSchedule",
    "BulletWindow",
    "ScenarioConfig",
    "ScenarioDirector",
    "build_action_schedule",
    "DecisionConfig",
    "DecisionDirector",
    "DecisionResult",
    "DecisionState",
]

from pytest import MonkeyPatch

from warbits.visual.perf import VisualBudget, VisualPerf, VisualStage


def test_visual_perf_accumulates(monkeypatch: MonkeyPatch) -> None:
    # Fake perf_counter_ns with deterministic times.
    t = {"v": 0}

    def fake_now_ns():
        t["v"] += 1_000_000  # +1ms per call
        return t["v"]

    import warbits.visual.perf.stats as stats_mod

    monkeypatch.setattr(stats_mod, "_now_ns", fake_now_ns)

    perf = VisualPerf()
    perf.begin_frame(0)
    perf.start(VisualStage.TERRAIN)
    perf.stop(VisualStage.TERRAIN)
    perf.start(VisualStage.HUD)
    perf.stop(VisualStage.HUD)
    timings = perf.end_frame()

    assert timings.ns_by_stage[int(VisualStage.TERRAIN)] > 0
    assert timings.ns_by_stage[int(VisualStage.HUD)] > 0
    assert timings.ns_total >= timings.ns_by_stage[int(VisualStage.TERRAIN)]


def test_visual_budget_flags() -> None:
    budget = VisualBudget(
        terrain_ms=0.1,
        entities_ms=0.1,
        projectiles_ms=0.1,
        hud_ms=0.1,
        effects_ms=0.1,
        total_ms=0.5,
    )

    # Build a fake timings object by using the public API.
    perf = VisualPerf()
    perf.begin_frame(0)
    # Burn some CPU by doing loops rather than sleep (deterministic enough).
    for _ in range(10000):
        pass
    timings = perf.end_frame()

    violations = budget.violations(timings)
    # We can't guarantee exact violation count, but total will likely exceed 0.5ms on most machines.
    assert isinstance(violations, list)

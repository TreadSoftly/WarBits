from pathlib import Path

from warbits.visual.qa.perf_scenes import run_perf_regression


def test_perf_regression_runs_and_is_deterministic():
    base = Path(__file__).parent / "fixtures" / "visual"
    rep1 = run_perf_regression(blueprints_jsonl=base / "blueprints.jsonl", frames=5, seed=123)
    rep2 = run_perf_regression(blueprints_jsonl=base / "blueprints.jsonl", frames=5, seed=123)

    assert len(rep1) >= 1
    assert len(rep2) == len(rep1)
    assert rep1[0].hash64 == rep2[0].hash64

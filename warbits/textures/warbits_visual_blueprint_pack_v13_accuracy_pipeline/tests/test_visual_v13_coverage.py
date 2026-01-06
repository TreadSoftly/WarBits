from pathlib import Path

from warbits.visual.qa.coverage import build_coverage_report


def test_coverage_counts_missing_weapon():
    base = Path(__file__).parent / "fixtures" / "visual"
    report = build_coverage_report(
        data_dir=base / "data",
        visual_map_path=base / "visual_map.json",
        blueprint_db_path=base / "blueprints.jsonl",
    )
    # vehicles: both are in map
    assert report.kinds["vehicle"].missing == 0
    # weapons: fixture weapon isn't mapped
    assert report.kinds["weapon"].missing == 1
    assert "weapon:test_missile" in report.kinds["weapon"].missing_ids

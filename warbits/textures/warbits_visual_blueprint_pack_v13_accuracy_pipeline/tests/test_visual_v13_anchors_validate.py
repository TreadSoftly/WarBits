from pathlib import Path

from warbits.visual.qa.anchors_validate import validate_anchors_jsonl


def test_anchors_validate_ok():
    base = Path(__file__).parent / "fixtures" / "visual"
    res = validate_anchors_jsonl(
        anchors_jsonl_path=base / "anchors.jsonl",
        blueprints_jsonl_path=base / "blueprints.jsonl",
    )
    assert res.ok

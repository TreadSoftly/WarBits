from pathlib import Path

from warbits.visual.qa.schema_validate import validate_blueprints_jsonl


def test_schema_validate_ok():
    base = Path(__file__).parent / "fixtures" / "visual"
    res = validate_blueprints_jsonl(base / "blueprints.jsonl")
    assert res.ok, "expected fixture blueprints to validate"
    assert res.total_records == 2

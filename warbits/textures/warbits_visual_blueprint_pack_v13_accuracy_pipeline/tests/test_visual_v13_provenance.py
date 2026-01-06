from pathlib import Path

from warbits.visual.qa.provenance import check_provenance


def test_provenance_strict_ok_for_fixture():
    base = Path(__file__).parent / "fixtures" / "visual"
    rep = check_provenance(
        blueprints_jsonl_path=base / "blueprints.jsonl",
        provenance_path=base / "provenance.jsonl",
        strict=True,
    )
    assert rep.ok

import json
import subprocess
import sys
from pathlib import Path


def test_pipeline_validate_runs(tmp_path):
    base = Path(__file__).parent / "fixtures" / "visual"
    artifacts = tmp_path / "artifacts"
    cmd = [
        sys.executable,
        "-m",
        "warbits.visual.tools.pipeline",
        "validate",
        "--blueprints",
        str(base / "blueprints.jsonl"),
        "--anchors",
        str(base / "anchors.jsonl"),
        "--artifacts",
        str(artifacts),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr
    rep_path = artifacts / "validate_report.json"
    assert rep_path.exists()
    rep = json.loads(rep_path.read_text(encoding="utf-8"))
    assert rep["ok"] is True

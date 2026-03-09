from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_schema_validate_cli_accepts_valid_artifact(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    tool = repo_root / "tools" / "schema_validate" / "main.py"
    payload = {
        "schema_name": "feature_space.v1",
        "schema_version": 1,
        "feature_space_id": "fs:test",
        "feature_space_type": "sae",
        "producer": "unit",
        "producer_version": "v1",
        "model_id": "tiny",
        "layer_map": {"0": "sae"},
        "dim": 2,
        "activation_rule": "topk",
        "checksum": "abc",
    }
    path = tmp_path / "feature_space.v1.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(tool), "--path", str(path)],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "valid:" in proc.stdout


def test_artifact_diff_cli_reports_changes(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    tool = repo_root / "tools" / "artifact_diff" / "main.py"

    left = {"a": 1, "b": 2}
    right = {"a": 1, "b": 3, "c": 4}
    left_path = tmp_path / "left.json"
    right_path = tmp_path / "right.json"
    left_path.write_text(json.dumps(left), encoding="utf-8")
    right_path.write_text(json.dumps(right), encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(tool), "--left", str(left_path), "--right", str(right_path), "--format", "json"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 1
    out = json.loads(proc.stdout)
    assert out["equal"] is False
    assert out["changes"]

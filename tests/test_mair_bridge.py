from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "core" / "protocol" / "python") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "core" / "protocol" / "python"))

pytest.importorskip("blt")
pytest.importorskip("mair")

from blt.export import run_trace
from blt.export import run_analysis
from featurecircuit_protocol.mair_bridge import mair_manifest_to_hif_legacy, mair_manifest_to_hif_v0


def test_mair_bridge_exports_hif_shapes(tmp_path: Path) -> None:
    manifest_path = run_trace("FeatureCircuit bridges MAIR.", "trace-fc-1", tmp_path, backend="mock")
    manifest_path = run_analysis(manifest_path)
    modern = mair_manifest_to_hif_v0(manifest_path)
    legacy = mair_manifest_to_hif_legacy(manifest_path)
    assert modern["schema"] == "HIF-v0"
    assert modern["hyperedges"]
    assert legacy["network-type"] == "hypergraph"
    assert legacy["edges"]

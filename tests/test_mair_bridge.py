from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "core" / "protocol" / "python") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "core" / "protocol" / "python"))

pytest.importorskip("mech_lab")

import mech_lab as ml
import mech_lab.api as ml_api
from featurecircuit_protocol.mair_bridge import mair_manifest_to_hif_legacy, mair_manifest_to_hif_v0


@pytest.mark.parametrize(
    ("family", "model", "profile"),
    (
        ("qwen3.5", "qwen3.5-2b", "qwen3.5-hybrid"),
        ("llama3.2", "llama3.2-3b", "llama3.2-hybrid"),
    ),
)
def test_mair_bridge_exports_hif_shapes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    family: str,
    model: str,
    profile: str,
) -> None:
    monkeypatch.setattr(ml_api, "_resolve_live_backend_for_lane", lambda _lane_key: "mock")

    bundle = ml.trace(
        "FeatureCircuit bridges MAIR.",
        output_dir=tmp_path / family,
        trace_id=f"trace-fc-{family}",
        family=family,
        model=model,
    )
    analysis = ml.analyze(bundle, output_dir=tmp_path / family, profile=profile)

    modern = mair_manifest_to_hif_v0(analysis.manifest_path)
    legacy = mair_manifest_to_hif_legacy(analysis.manifest_path)
    assert modern["schema"] == "HIF-v0"
    assert modern["hyperedges"]
    assert legacy["network-type"] == "hypergraph"
    assert legacy["edges"]

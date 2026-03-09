from __future__ import annotations

import pytest

from featurecircuit_protocol.compatibility import CompatibilityError, assert_stage_compatible, check_stage_compatibility


def _manifest() -> dict:
    return {
        "schema_name": "protocol_manifest.v1",
        "schema_version": 1,
        "protocol_version": "featurecircuit-protocol.v1",
        "run_id": "run-1",
        "artifact_schema_versions": {
            "activation_batch": "activation_batch.v1",
            "feature_space": "feature_space.v1",
            "feature_events": "feature_events.v1",
            "relations": "relations.v1",
            "structures": "structures.v1",
            "candidates": "candidates.v1",
            "circuit_snapshot": "circuit_snapshot.v1",
            "scores": "scores.v1",
        },
        "export_profiles": ["hypercircuit_handoff.v1", "hif.v0"],
        "lineage": {"run_id": "run-1"},
    }


def test_stage_compatibility_passes_for_matching_inputs() -> None:
    errors = check_stage_compatibility(
        protocol_manifest=_manifest(),
        required_schema_versions={"feature_space": "feature_space.v1", "scores": "scores.v1"},
        feature_space={
            "feature_space_id": "fs:1",
            "model_id": "tiny-gpt2",
            "layer_map": {"0": "sae", "1": "sae"},
        },
        expected_feature_space_id="fs:1",
        expected_model_id="tiny-gpt2",
        expected_layers=[0],
        candidate_set={"candidates": [{"arity": 2}]},
        max_candidate_arity=3,
        score_bundle={"scores": [{"coactivation_score": 1.0, "final_rank_score": 1.0}]},
        required_score_fields=["coactivation_score", "final_rank_score"],
    )
    assert errors == []


def test_stage_compatibility_collects_mismatches() -> None:
    errors = check_stage_compatibility(
        protocol_manifest=_manifest(),
        required_schema_versions={"feature_space": "feature_space.v2"},
        feature_space={
            "feature_space_id": "fs:other",
            "model_id": "other-model",
            "layer_map": {"3": "sae"},
        },
        expected_feature_space_id="fs:1",
        expected_model_id="tiny-gpt2",
        expected_layers=[0],
        candidate_set={"candidates": [{"arity": 5}]},
        max_candidate_arity=3,
        score_bundle={"scores": [{}]},
        required_score_fields=["coactivation_score"],
    )
    assert len(errors) >= 5
    joined = " ".join(errors)
    assert "schema version mismatch" in joined
    assert "feature_space_id mismatch" in joined
    assert "model_id mismatch" in joined
    assert "layer compatibility failure" in joined
    assert "candidate arity unsupported" in joined
    assert "missing required fields" in joined


def test_assert_stage_compatible_raises_on_failure() -> None:
    with pytest.raises(CompatibilityError):
        assert_stage_compatible(
            protocol_manifest=_manifest(),
            required_schema_versions={"feature_space": "feature_space.v2"},
        )

from __future__ import annotations

from pathlib import Path

from featurecircuit_protocol.artifacts import (
    CandidateSetArtifact,
    FeatureEvent,
    FeatureEventStream,
    FeatureSpaceDescriptor,
    ProtocolManifest,
    RelationArtifact,
    ScoreBundleArtifact,
    StructureArtifact,
)
from featurecircuit_protocol.io import write_json, write_jsonl
from featurecircuit_protocol.validation import validate_json_file, validate_jsonl_file, validate_payload


def test_schema_validation_roundtrip(tmp_path: Path) -> None:
    fs = FeatureSpaceDescriptor(
        feature_space_id="fs:demo",
        feature_space_type="sae",
        producer="demo",
        producer_version="v1",
        model_id="tiny-gpt2",
        layer_map={"0": "sae0"},
        dim=4,
        activation_rule="topk",
        checksum="abc123",
    ).to_dict()
    validate_payload(fs, "feature_space.v1.json")
    fs_path = tmp_path / "feature_space.v1.json"
    write_json(fs_path, fs)
    validate_json_file(fs_path, "feature_space.v1.json")

    stream = FeatureEventStream(
        run_id="run-a",
        source_kind="mock",
        feature_space_id="fs:demo",
        feature_space_version="v1",
        events=[
            FeatureEvent(
                run_id="run-a",
                event_id="e1",
                source_kind="mock",
                feature_space_id="fs:demo",
                feature_space_version="v1",
                sample_id="s0",
                token_index=0,
                layer=0,
                node_type="sae_features",
                node_id="12",
                value=1.0,
                step_index=0,
            )
        ],
    )
    events_path = tmp_path / "feature_events.v1.jsonl"
    write_jsonl(events_path, stream.to_jsonl_rows())
    validate_jsonl_file(events_path, "feature_events.v1.jsonl")

    rel = RelationArtifact(
        run_id="run-a",
        relation_builder_type="coactivation",
        relation_builder_version="v1",
        feature_space_id="fs:demo",
        relations=[
            {
                "relation_id": "r1",
                "relation_type": "coactivation",
                "members": ["f1", "f2"],
                "arity": 2,
                "directionality": "undirected",
                "weight": 1.0,
            }
        ],
    ).to_dict()
    validate_payload(rel, "relations.v1.json")

    struct = StructureArtifact(
        run_id="run-a",
        structure_builder_type="hypergraph",
        structure_builder_version="v1",
        structures=[
            {
                "structure_id": "s1",
                "structure_type": "hyperedge",
                "members": ["1", "2"],
                "arity": 2,
            }
        ],
    ).to_dict()
    validate_payload(struct, "structures.v1.json")

    candidates = CandidateSetArtifact(
        run_id="run-a",
        candidates=[
            {
                "candidate_id": "c1",
                "candidate_type": "hyperedge",
                "members": ["1", "2"],
                "arity": 2,
                "support_count": 4,
                "stability_score": 0.1,
                "synergy_score": 0.2,
                "formation_rule": "demo",
            }
        ],
    ).to_dict()
    validate_payload(candidates, "candidates.v1.json")

    scores = ScoreBundleArtifact(
        run_id="run-a",
        scores=[
            {
                "candidate_id": "c1",
                "coactivation_score": 4.0,
                "stability_score": 0.1,
                "synergy_score": 0.2,
                "calibration_score": 0.0,
                "causal_score": 0.0,
                "final_rank_score": 4.3,
            }
        ],
    ).to_dict()
    validate_payload(scores, "scores.v1.json")

    manifest = ProtocolManifest(
        protocol_version="featurecircuit-protocol.v1",
        run_id="run-a",
        artifact_schema_versions={"feature_events": "feature_events.v1"},
        package_versions={"py_nsi": "0.1.0"},
        compat_mode_enabled=True,
        hif_export_mode="legacy_demo",
        run_config_checksum="abc",
    ).to_dict()
    validate_payload(manifest, "protocol_manifest.v1.json")

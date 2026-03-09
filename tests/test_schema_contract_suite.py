from __future__ import annotations

import copy

import pytest

from featurecircuit_protocol.validation import validate_payload


def _payloads() -> dict[str, dict]:
    return {
        "activation_batch.v1.json": {
            "schema_name": "activation_batch.v1",
            "schema_version": 1,
            "activation_batch_id": "ab1",
            "run_id": "run-1",
            "training_run_id": "train-1",
            "checkpoint_id": "ckpt-1",
            "batch_id": "batch-0",
            "model_id": "tiny",
            "model_revision": "main",
            "tokenizer_id": "gpt2",
            "layer_targets": [0],
            "activation_kind": "residual",
            "shape_summary": {"batch": 1, "hidden": 2},
            "dtype": "float32",
            "device": "cpu",
        },
        "feature_space.v1.json": {
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
        },
        "feature_events.v1.jsonl": {
            "schema_name": "feature_events.v1",
            "schema_version": 1,
            "run_id": "run-1",
            "event_id": "e1",
            "source_kind": "mock",
            "feature_space_id": "fs:test",
            "feature_space_version": "v1",
            "sample_id": "s1",
            "token_index": 0,
            "layer": 0,
            "node_type": "sae_features",
            "node_id": "1",
            "value": 1.0,
            "step_index": 0,
            "metadata": {"trace": "unit"},
        },
        "relations.v1.json": {
            "schema_name": "relations.v1",
            "schema_version": 1,
            "run_id": "run-1",
            "relation_builder_type": "coactivation",
            "relation_builder_version": "v1",
            "feature_space_id": "fs:test",
            "metadata": {"lane": "unit"},
            "relations": [
                {
                    "relation_id": "r1",
                    "relation_type": "coactivation",
                    "members": ["1", "2"],
                    "arity": 2,
                    "weight": 1.0,
                }
            ],
        },
        "structures.v1.json": {
            "schema_name": "structures.v1",
            "schema_version": 1,
            "run_id": "run-1",
            "structure_builder_type": "hypergraph",
            "structure_builder_version": "v1",
            "metadata": {"lane": "unit"},
            "structures": [
                {
                    "structure_id": "s1",
                    "structure_type": "hyperedge",
                    "members": ["1", "2"],
                    "arity": 2,
                }
            ],
        },
        "candidates.v1.json": {
            "schema_name": "candidates.v1",
            "schema_version": 1,
            "run_id": "run-1",
            "metadata": {"lane": "unit"},
            "candidates": [
                {
                    "candidate_id": "c1",
                    "candidate_type": "hyperedge",
                    "members": ["1", "2"],
                    "arity": 2,
                    "support_count": 1,
                    "stability_score": 0.1,
                    "synergy_score": 0.2,
                    "formation_rule": "unit",
                }
            ],
        },
        "circuit_snapshot.v1.json": {
            "schema_name": "circuit_snapshot.v1",
            "schema_version": 1,
            "snapshot_id": "snap-1",
            "run_id": "run-1",
            "training_run_id": "train-1",
            "checkpoint_id": "ckpt-1",
            "feature_space_id": "fs:test",
            "relation_artifact_id": "rel-1",
            "structure_artifact_id": "struct-1",
            "candidate_set_id": "cand-1",
            "candidate_ids": ["c1"],
            "summary": {"note": "ok"},
        },
        "scores.v1.json": {
            "schema_name": "scores.v1",
            "schema_version": 1,
            "run_id": "run-1",
            "metadata": {"lane": "unit"},
            "scores": [
                {
                    "candidate_id": "c1",
                    "coactivation_score": 1.0,
                    "stability_score": 0.1,
                    "synergy_score": 0.1,
                    "calibration_score": 0.0,
                    "causal_score": 0.0,
                    "final_rank_score": 1.2,
                }
            ],
        },
        "protocol_manifest.v1.json": {
            "schema_name": "protocol_manifest.v1",
            "schema_version": 1,
            "protocol_version": "featurecircuit-protocol.v1",
            "run_id": "run-1",
            "artifact_schema_versions": {"feature_space": "feature_space.v1"},
            "package_versions": {"py_nsi": "0.1.0"},
            "compat_mode_enabled": False,
            "hif_export_mode": "both",
            "run_config_checksum": "abc",
            "export_profiles": ["hypercircuit_handoff.v1", "hif.v0"],
            "lineage": {"run_id": "run-1", "training_run_id": "train-1", "checkpoint_id": "ckpt-1"},
        },
        "hif.v0.json": {
            "schema": "HIF-v0",
            "nodes": [{"id": "1"}, {"id": "2"}],
            "hyperedges": [{"id": "he_1", "nodes": ["1", "2"], "count": 1}],
        },
        "hif_legacy_demo.v0.json": {
            "network-type": "hypergraph",
            "nodes": [{"id": 1}, {"id": 2}],
            "edges": [{"id": 0, "key": [1, 2], "observation_count": 1, "stii_weight": 0.0}],
            "incidences": [{"edge": 0, "nodes": [1, 2]}],
        },
    }


def test_each_schema_accepts_valid_payload() -> None:
    for schema_name, payload in _payloads().items():
        validate_payload(payload, schema_name)


def test_each_schema_rejects_missing_required_field() -> None:
    for schema_name, payload in _payloads().items():
        bad = copy.deepcopy(payload)
        if schema_name == "feature_events.v1.jsonl":
            bad.pop("event_id")
        elif schema_name == "hif.v0.json":
            bad.pop("hyperedges")
        elif schema_name == "hif_legacy_demo.v0.json":
            bad.pop("incidences")
        elif schema_name == "protocol_manifest.v1.json":
            bad.pop("lineage")
        elif schema_name == "activation_batch.v1.json":
            bad.pop("activation_batch_id")
        elif schema_name == "circuit_snapshot.v1.json":
            bad.pop("snapshot_id")
        else:
            bad.pop("schema_name")
        with pytest.raises(Exception):
            validate_payload(bad, schema_name)

from __future__ import annotations

from pathlib import Path

from featurecircuit_protocol.validation import validate_json_file
from python.repro.protocol_manifest import (
    build_snapshot_id,
    build_structure_id,
    build_candidate_id,
    build_feature_key,
    build_member_key,
    build_relation_id,
    write_activation_batch,
    write_candidates,
    write_circuit_snapshot,
    write_feature_space,
    write_hif_exports,
    write_protocol_manifest,
    write_relations,
    write_scores,
    write_structures,
)


def test_demo_protocol_writers(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-1"
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = write_protocol_manifest(
        run_dir=str(run_dir),
        config_payload={"hello": "world"},
        compat_mode_enabled=False,
        hif_export_mode="both",
    )
    validate_json_file(manifest_path, "protocol_manifest.v1.json")

    feature_space_path = write_feature_space(
        str(run_dir),
        {
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
    )
    validate_json_file(feature_space_path, "feature_space.v1.json")

    activation_batch_path = write_activation_batch(
        str(run_dir),
        {
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
    )
    validate_json_file(activation_batch_path, "activation_batch.v1.json")

    relations_path = write_relations(
        str(run_dir),
        {
            "schema_name": "relations.v1",
            "schema_version": 1,
            "run_id": "run-1",
            "relation_builder_type": "coactivation",
            "relation_builder_version": "v1",
            "feature_space_id": "fs:test",
            "relations": [
                {
                    "relation_id": "r1",
                    "relation_type": "coactivation",
                    "members": ["1", "2"],
                    "arity": 2,
                    "directionality": "undirected",
                    "weight": 1.0,
                }
            ],
        },
    )
    validate_json_file(relations_path, "relations.v1.json")

    structures_path = write_structures(
        str(run_dir),
        {
            "schema_name": "structures.v1",
            "schema_version": 1,
            "run_id": "run-1",
            "structure_builder_type": "hypergraph",
            "structure_builder_version": "v1",
            "structures": [
                {
                    "structure_id": "s1",
                    "structure_type": "hyperedge",
                    "members": ["1", "2"],
                    "arity": 2,
                }
            ],
        },
    )
    validate_json_file(structures_path, "structures.v1.json")
    canonical_hif, legacy_hif = write_hif_exports(
        str(run_dir),
        {
            "schema_name": "structures.v1",
            "schema_version": 1,
            "run_id": "run-1",
            "structure_builder_type": "hypergraph",
            "structure_builder_version": "v1",
            "structures": [
                {
                    "structure_id": "s1",
                    "structure_type": "hyperedge",
                    "members": ["1", "2"],
                    "arity": 2,
                    "support_count": 2,
                }
            ],
        },
    )
    validate_json_file(canonical_hif, "hif.v0.json")
    validate_json_file(legacy_hif, "hif_legacy_demo.v0.json")

    candidates_path = write_candidates(
        str(run_dir),
        {
            "schema_name": "candidates.v1",
            "schema_version": 1,
            "run_id": "run-1",
            "candidates": [
                {
                    "candidate_id": "c1",
                    "candidate_type": "hyperedge",
                    "members": ["1", "2"],
                    "arity": 2,
                    "support_count": 5,
                    "stability_score": 0.5,
                    "synergy_score": 0.5,
                    "formation_rule": "unit",
                }
            ],
        },
    )
    validate_json_file(candidates_path, "candidates.v1.json")

    circuit_snapshot_path = write_circuit_snapshot(
        str(run_dir),
        {
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
            "summary": {"note": "unit"},
        },
    )
    validate_json_file(circuit_snapshot_path, "circuit_snapshot.v1.json")

    scores_path = write_scores(
        str(run_dir),
        {
            "schema_name": "scores.v1",
            "schema_version": 1,
            "run_id": "run-1",
            "scores": [
                {
                    "candidate_id": "c1",
                    "coactivation_score": 1.0,
                    "stability_score": 1.0,
                    "synergy_score": 1.0,
                    "calibration_score": 1.0,
                    "causal_score": 1.0,
                    "final_rank_score": 1.0,
                }
            ],
        },
    )
    validate_json_file(scores_path, "scores.v1.json")

    assert Path(manifest_path).exists()
    assert Path(feature_space_path).exists()
    assert Path(relations_path).exists()
    assert Path(structures_path).exists()
    assert Path(candidates_path).exists()
    assert Path(scores_path).exists()
    assert Path(activation_batch_path).exists()
    assert Path(circuit_snapshot_path).exists()


def test_demo_protocol_id_helpers_are_deterministic() -> None:
    mk1 = build_member_key("fs:test", 0, "hyperedge", "1|2")
    mk2 = build_member_key("fs:test", 0, "hyperedge", "1|2")
    fk = build_feature_key("fs:test", 0, "hyperedge", "1|2")
    assert mk1 == mk2
    assert fk == mk1

    rel1 = build_relation_id(
        relation_builder_type="temporal_coactivation",
        relation_builder_version="v1",
        member_feature_ids_ordered=["f1", "f2"],
        directionality="undirected",
        arity=2,
        construction_rule="gse_window",
        threshold=0.05,
    )
    rel2 = build_relation_id(
        relation_builder_type="temporal_coactivation",
        relation_builder_version="v1",
        member_feature_ids_ordered=["f1", "f2"],
        directionality="undirected",
        arity=2,
        construction_rule="gse_window",
        threshold=0.05,
    )
    assert rel1 == rel2

    c1 = build_candidate_id(
        structure_builder_type="temporal_hypergraph",
        structure_builder_version="v1",
        member_feature_ids=["f2", "f1"],
        candidate_type="hyperedge",
        arity=2,
    )
    c2 = build_candidate_id(
        structure_builder_type="temporal_hypergraph",
        structure_builder_version="v1",
        member_feature_ids=["f1", "f2"],
        candidate_type="hyperedge",
        arity=2,
    )
    assert c1 == c2

    s1 = build_structure_id("temporal_hypergraph", "v1", ["f1", "f2"], "hyperedge")
    s2 = build_structure_id("temporal_hypergraph", "v1", ["f2", "f1"], "hyperedge")
    assert s1 == s2

    snap1 = build_snapshot_id("train-1", "ckpt-1", "fs:test", "cand-1")
    snap2 = build_snapshot_id("train-1", "ckpt-1", "fs:test", "cand-1")
    assert snap1 == snap2

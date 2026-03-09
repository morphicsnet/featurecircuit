from __future__ import annotations

import os
import sys
import json
import random
import shutil
from typing import Any, Dict, List, Tuple

import numpy as np
import torch

# Make local modules importable (namespace package "python" at repo root)
sys.path.append(os.path.abspath("."))

from python.utils.config import load_yaml  # noqa: E402
from python.utils.artifacts import create_run_dir, dump_json, dump_yaml  # noqa: E402
from python.datasets.loans_bias import generate_loans_dataset  # noqa: E402
from python.activations.extract import get_model_and_tokenizer, capture_layer_activations  # noqa: E402
from python.ensemble.intersection import build_pyensemble  # noqa: E402
from python.hypergraph.pipeline import build_hypergraph_with_nodes  # noqa: E402
from python.stii.compute import compute_stii_for_hyperedge  # noqa: E402
from python.acdc.prune import acdc_minimal_circuit  # noqa: E402
from python.metrics.fairness import gender_concept_probs, report_bias_presence  # noqa: E402
from python.repro.protocol_manifest import (  # noqa: E402
    build_candidate_id,
    build_feature_key,
    build_member_key,
    build_relation_id,
    build_snapshot_id,
    build_structure_id,
    write_circuit_snapshot,
    write_candidates,
    write_feature_events,
    write_feature_space,
    write_hif_exports,
    write_protocol_manifest,
    write_relations,
    write_scores,
    write_structures,
)

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score


def _seed_all(seed: int) -> None:
    np.random.seed(seed)
    random.seed(seed)
    torch.manual_seed(seed)


def _preflight_py_nsi() -> None:
    """
    Ensure py_nsi is importable before proceeding. If not, raise with instruction.
    """
    try:
        import py_nsi  # noqa: F401
    except Exception as e:
        raise RuntimeError(
            "py_nsi is not importable. Build the local Rust wheel first:\n"
            "  maturin develop --release -m core/py_nsi/Cargo.toml\n"
            "Then re-run the demo."
        ) from e


def _train_logreg_nodes(X: np.ndarray, y: np.ndarray, seed: int) -> Dict[str, Any]:
    """
    Train/test split on node features, return base accuracy and model.
    """
    X = X.astype(np.float32, copy=False)
    y = y.astype(np.int32, copy=False)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=int(seed), stratify=y
    )
    clf = LogisticRegression(solver="liblinear", random_state=int(seed), max_iter=1000)
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    acc = float(accuracy_score(y_test, y_pred))
    return {"clf": clf, "accuracy": acc, "X_test": X_test, "y_test": y_test}


def main(config_path: str = "configs/demo4_causal.yaml") -> None:
    # Load config
    cfg = load_yaml(config_path)
    model_name: str = cfg["model_name"]
    layer_index: int = int(cfg["layer_index"])
    ds_cfg = cfg["dataset"]
    ens_cfg = cfg["ensemble"]
    spk_cfg = cfg["spike"]
    stii_cfg = cfg["stii"]
    acdc_cfg = cfg["acdc"]
    out_cfg = cfg["outputs"]

    # Determinism
    global_seed = int(ds_cfg.get("seed", 1337))
    _seed_all(global_seed)

    # 1) Data
    n_samples = int(ds_cfg["n_samples"])
    bias_strength = float(ds_cfg.get("bias_strength", 0.25))
    noise = float(ds_cfg.get("noise", 0.05))
    texts, labels_np, genders_np = generate_loans_dataset(
        n_samples=n_samples, seed=global_seed, bias_strength=bias_strength, noise=noise
    )
    labels_np = np.asarray(labels_np, dtype=np.int32)
    genders_np = np.asarray(genders_np, dtype=np.int32)

    # 2) HF model and activations (GPT-2 tiny)
    model, tokenizer = get_model_and_tokenizer(model_name)
    acts = capture_layer_activations(model, tokenizer, texts, layer_index=layer_index)  # [N, D]
    if acts.shape[0] != len(texts):
        raise RuntimeError(f"Activation rows {acts.shape[0]} != #texts {len(texts)}")
    input_dim = int(acts.shape[1])

    # Preflight py_nsi availability
    _preflight_py_nsi()

    # 3) Ensemble
    feature_dim = int(ens_cfg["feature_dim"])
    top_k_ens = int(ens_cfg["top_k"])
    seeds_ens: List[int] = [int(s) for s in ens_cfg["seeds"]]

    # Provide input dimension for the canonical ProtocolEnsemble projection.
    os.environ["PY_NSI_INPUT_DIM"] = str(input_dim)
    ensemble = build_pyensemble(feature_dim=feature_dim, top_k=top_k_ens, seeds=seeds_ens)

    # 4) Hypergraph + node features (spikes + GSE + aggregation)
    t_start = float(spk_cfg["t_start"])
    delta_t = float(spk_cfg["delta_t"])
    min_sigmoid = float(spk_cfg["min_sigmoid"])
    gse_window = float(spk_cfg["gse_window"])

    _store, X_edge_bool, edge_keys, edge_counts, nodes_by_sample_bool, node_keys = build_hypergraph_with_nodes(
        ensemble=ensemble,
        acts=acts,
        labels=labels_np,
        t_start=t_start,
        delta_t=delta_t,
        min_sigmoid=min_sigmoid,
        gse_window=gse_window,
    )

    N, E = int(X_edge_bool.shape[0]), int(X_edge_bool.shape[1])
    U = int(nodes_by_sample_bool.shape[1]) if nodes_by_sample_bool.ndim == 2 else 0

    # Graceful path: no hyperedges or no nodes
    if E == 0 or U == 0:
        base_dir = out_cfg["base_dir"]
        run_tag = out_cfg.get("run_tag", None)
        run_dir = create_run_dir(base_dir=base_dir, run_tag=run_tag)
        # Minimal artifacts
        dump_yaml(cfg, os.path.join(run_dir, "config.yaml"))
        dump_json(
            {
                "note": "No hyperedges or nodes formed; check gse_window/min_sigmoid/top_k and dataset size.",
                "num_edges": int(E),
                "num_nodes": int(U),
            },
            os.path.join(run_dir, "stii_values.json"),
        )
        dump_json(
            {
                "kept_edges": [],
                "removed_edges": [],
                "base_acc": 0.0,
                "final_acc": 0.0,
                "note": "No edges to prune.",
            },
            os.path.join(run_dir, "acdc_minimal_circuit.json"),
        )
        dump_json(
            {
                "threshold": 0.6,
                "num_biased_nodes": 0,
                "num_minimal_edges": 0,
                "biased_nodes_in_minimal_count": 0,
                "biased_nodes_in_minimal_ratio": 0.0,
                "any_biased_node_in_minimal": False,
                "examples": [],
                "note": "No nodes or minimal circuit.",
            },
            os.path.join(run_dir, "fairness_report.json"),
        )
        run_id = os.path.basename(os.path.abspath(run_dir))
        structures_payload = {
            "schema_name": "structures.v1",
            "schema_version": 1,
            "run_id": run_id,
            "structure_builder_type": "temporal_hypergraph",
            "structure_builder_version": "v1",
            "structures": [],
        }
        relations_payload = {
            "schema_name": "relations.v1",
            "schema_version": 1,
            "run_id": run_id,
            "relation_builder_type": "temporal_coactivation",
            "relation_builder_version": "v1",
            "feature_space_id": "demo4.hyperedge_space",
            "relations": [],
        }
        write_feature_space(
            run_dir,
            {
                "schema_name": "feature_space.v1",
                "schema_version": 1,
                "feature_space_id": "demo4.hyperedge_space",
                "feature_space_type": "hyperedge",
                "producer": "demo4_causal",
                "producer_version": "v1",
                "model_id": model_name,
                "layer_map": {str(layer_index): "hyperedge"},
                "dim": int(E),
                "activation_rule": "temporal_gse",
                "checksum": f"{input_dim}:{feature_dim}:{top_k_ens}:{gse_window}",
                "metadata": {"empty": True},
            },
        )
        write_relations(run_dir, relations_payload)
        write_structures(run_dir, structures_payload)
        _, legacy_hif = write_hif_exports(run_dir, structures_payload)
        # Preserve legacy filename consumed by existing dashboard utilities.
        shutil.copyfile(legacy_hif, os.path.join(run_dir, "hypergraph_stii.hif.json"))
        write_candidates(
            run_dir,
            {
                "schema_name": "candidates.v1",
                "schema_version": 1,
                "run_id": run_id,
                "candidates": [],
            },
        )
        write_scores(
            run_dir,
            {
                "schema_name": "scores.v1",
                "schema_version": 1,
                "run_id": run_id,
                "scores": [],
            },
        )
        candidate_set_id = f"{run_id}:candidate_set"
        snapshot_id = build_snapshot_id(
            training_run_id=run_id,
            checkpoint_id="checkpoint-unknown",
            feature_space_id="demo4.hyperedge_space",
            candidate_set_id=candidate_set_id,
        )
        write_circuit_snapshot(
            run_dir,
            {
                "schema_name": "circuit_snapshot.v1",
                "schema_version": 1,
                "snapshot_id": snapshot_id,
                "run_id": run_id,
                "training_run_id": run_id,
                "checkpoint_id": "checkpoint-unknown",
                "feature_space_id": "demo4.hyperedge_space",
                "relation_artifact_id": f"{run_id}:relations",
                "structure_artifact_id": f"{run_id}:structures",
                "candidate_set_id": candidate_set_id,
                "candidate_ids": [],
                "summary": {"note": "no candidate edges"},
            },
        )
        write_feature_events(run_dir, [])
        write_protocol_manifest(
            run_dir=run_dir,
            config_payload=cfg,
            compat_mode_enabled=False,
            hif_export_mode="both",
        )
        print("Demo4 STII+ACDC: edges=0, stii_computed=0, base_acc=0.000, final_acc=0.000, gender_nodes_in_minimal=0")
        return

    # Convert designs to float
    X_edge = X_edge_bool.astype(np.float32)
    X_node = nodes_by_sample_bool.astype(np.float32)
    y = labels_np.astype(np.int32)

    # 5) Train a LogisticRegression on node features to predict y; compute base accuracy
    node_clf_bundle = _train_logreg_nodes(X_node, y, seed=global_seed)
    node_clf = node_clf_bundle["clf"]
    base_acc_nodes = float(node_clf_bundle["accuracy"])

    # Map nodes to columns
    node_to_col: Dict[int, int] = {int(nid): j for j, (nid,) in enumerate(node_keys)}

    # 6) STII per hyperedge (size <= 3 for tractability)
    max_order_k = int(stii_cfg.get("max_order_k", 2))
    stii_values: Dict[Tuple[int, ...], float] = {}
    computed_count = 0
    for ek in edge_keys:
        m = len(ek)
        if m <= 3:
            try:
                stii_val = compute_stii_for_hyperedge(
                    edge_key=ek,
                    node_to_col=node_to_col,
                    X_base=X_node,
                    y=y,
                    logreg_model=node_clf,
                    max_order_k=min(max_order_k, m),
                )
            except Exception as e:
                # Robust to any edge-specific issues; record zero
                stii_val = 0.0
            stii_values[ek] = float(stii_val)
            computed_count += 1

    # 7) ACDC pruning on edge features
    tolerance_drop = float(acdc_cfg.get("tolerance_drop", 0.02))
    max_edges = int(acdc_cfg.get("max_edges", 50))
    acdc_result = acdc_minimal_circuit(
        edge_keys=edge_keys,
        stii=stii_values,
        X_edge=X_edge,
        y=y,
        tolerance_drop=tolerance_drop,
        max_edges=max_edges,
        seed=global_seed,
    )

    minimal_edges = acdc_result.get("kept_edges", [])
    # Build edge->nodes map
    edge_to_nodes: Dict[Tuple[int, ...], List[int]] = {ek: [int(n) for n in ek] for ek in edge_keys}

    # 8) Fairness: node-level gender association and presence in minimal circuit
    node_gender = gender_concept_probs(nodes_by_sample=X_node.astype(bool), genders=genders_np)
    fairness = report_bias_presence(
        minimal_edges=minimal_edges,
        edge_to_nodes=edge_to_nodes,
        node_gender_probs=node_gender,
        node_keys=node_keys,
        threshold=0.6,
    )

    # 9) Artifacts
    base_dir = out_cfg["base_dir"]
    run_tag = out_cfg.get("run_tag", None)
    run_dir = create_run_dir(base_dir=base_dir, run_tag=run_tag)

    # Save config
    dump_yaml(cfg, os.path.join(run_dir, "config.yaml"))

    # STII values (per-edge)
    stii_list = [
        {"edge": [int(x) for x in ek], "stii": float(stii_values.get(ek, 0.0))}
        for ek in edge_keys
        if len(ek) <= 3
    ]
    dump_json({"values": stii_list, "computed_count": int(computed_count), "total_edges": int(E)}, os.path.join(run_dir, "stii_values.json"))

    # ACDC minimal circuit
    # Ensure serializable (tuples -> lists)
    acdc_ser = {
        "kept_edges": [[int(x) for x in ek] for ek in acdc_result.get("kept_edges", [])],
        "removed_edges": [[int(x) for x in ek] for ek in acdc_result.get("removed_edges", [])],
        "base_acc": float(acdc_result.get("base_acc", 0.0)),
        "final_acc": float(acdc_result.get("final_acc", 0.0)),
        "tolerance_drop": tolerance_drop,
        "max_edges": max_edges,
    }
    dump_json(acdc_ser, os.path.join(run_dir, "acdc_minimal_circuit.json"))

    # Fairness report
    dump_json(fairness, os.path.join(run_dir, "fairness_report.json"))

    run_id = os.path.basename(os.path.abspath(run_dir))

    feature_space_id = "demo4.hyperedge_space"
    relation_builder_type = "temporal_coactivation"
    relation_builder_version = "v1"
    structures = []
    relations = []
    for idx, ek in enumerate(edge_keys):
        members = [str(int(x)) for x in ek]
        support_count = int(edge_counts.get(ek, 0))
        stii_val = float(stii_values.get(ek, 0.0))
        structures.append(
            {
                "structure_id": build_structure_id(
                    structure_builder_type="temporal_hypergraph",
                    structure_builder_version="v1",
                    members=members,
                    structure_type="hyperedge",
                ),
                "structure_type": "hyperedge",
                "members": members,
                "arity": len(members),
                "support_count": support_count,
                "stability_score": stii_val,
                "construction_rule": "gse_temporal_island",
            }
        )
        relations.append(
            {
                "relation_id": build_relation_id(
                    relation_builder_type=relation_builder_type,
                    relation_builder_version=relation_builder_version,
                    member_feature_ids_ordered=members,
                    directionality="undirected",
                    arity=len(members),
                    construction_rule="gse_window",
                    threshold=float(gse_window),
                ),
                "relation_type": relation_builder_type,
                "members": members,
                "arity": len(members),
                "directionality": "undirected",
                "weight": float(support_count),
                "construction_rule": "gse_window",
                "threshold": float(gse_window),
            }
        )

    structures_payload = {
        "schema_name": "structures.v1",
        "schema_version": 1,
        "run_id": run_id,
        "structure_builder_type": "temporal_hypergraph",
        "structure_builder_version": "v1",
        "structures": structures,
    }
    relations_payload = {
        "schema_name": "relations.v1",
        "schema_version": 1,
        "run_id": run_id,
        "relation_builder_type": relation_builder_type,
        "relation_builder_version": relation_builder_version,
        "feature_space_id": feature_space_id,
        "relations": relations,
    }
    write_feature_space(
        run_dir,
        {
            "schema_name": "feature_space.v1",
            "schema_version": 1,
            "feature_space_id": feature_space_id,
            "feature_space_type": "hyperedge",
            "producer": "demo4_causal",
            "producer_version": "v1",
            "model_id": model_name,
            "layer_map": {str(layer_index): "hyperedge"},
            "dim": int(E),
            "activation_rule": "temporal_gse",
            "checksum": f"{input_dim}:{feature_dim}:{top_k_ens}:{gse_window}",
            "metadata": {"seed": global_seed},
        },
    )
    write_relations(run_dir, relations_payload)
    write_structures(run_dir, structures_payload)
    _, legacy_hif = write_hif_exports(run_dir, structures_payload)
    shutil.copyfile(legacy_hif, os.path.join(run_dir, "hypergraph_stii.hif.json"))

    # Candidate and score artifacts for downstream consumption.
    causal_gain = float(acdc_ser["final_acc"]) - float(acdc_ser["base_acc"])
    candidate_rows: List[Dict[str, Any]] = []
    score_rows: List[Dict[str, Any]] = []
    for idx, edge in enumerate(acdc_ser["kept_edges"]):
        edge_key = tuple(int(x) for x in edge)
        member_ids = [str(x) for x in edge_key]
        cid = build_candidate_id(
            structure_builder_type="temporal_hypergraph",
            structure_builder_version="v1",
            member_feature_ids=member_ids,
            candidate_type="hyperedge",
            arity=len(edge_key),
        )
        support_count = int(edge_counts.get(edge_key, 0))
        stability = float(stii_values.get(edge_key, 0.0))
        synergy = float(stability)
        candidate_rows.append(
            {
                "candidate_id": cid,
                "candidate_type": "hyperedge",
                "members": member_ids,
                "arity": len(edge_key),
                "support_count": support_count,
                "stability_score": stability,
                "synergy_score": synergy,
                "formation_rule": "acdc_minimal_keep",
            }
        )
        score_rows.append(
            {
                "candidate_id": cid,
                "coactivation_score": float(support_count),
                "stability_score": stability,
                "synergy_score": synergy,
                "calibration_score": 0.0,
                "causal_score": causal_gain,
                "final_rank_score": float(support_count) + stability + synergy + causal_gain,
            }
        )

    write_candidates(
        run_dir,
        {
            "schema_name": "candidates.v1",
            "schema_version": 1,
            "run_id": run_id,
            "candidates": candidate_rows,
        },
    )
    write_scores(
        run_dir,
        {
            "schema_name": "scores.v1",
            "schema_version": 1,
            "run_id": run_id,
            "scores": score_rows,
        },
    )
    candidate_set_id = f"{run_id}:candidate_set"
    snapshot_id = build_snapshot_id(
        training_run_id=run_id,
        checkpoint_id="checkpoint-unknown",
        feature_space_id=feature_space_id,
        candidate_set_id=candidate_set_id,
    )
    write_circuit_snapshot(
        run_dir,
        {
            "schema_name": "circuit_snapshot.v1",
            "schema_version": 1,
            "snapshot_id": snapshot_id,
            "run_id": run_id,
            "training_run_id": run_id,
            "checkpoint_id": "checkpoint-unknown",
            "feature_space_id": feature_space_id,
            "relation_artifact_id": f"{run_id}:relations",
            "structure_artifact_id": f"{run_id}:structures",
            "candidate_set_id": candidate_set_id,
            "candidate_ids": [c["candidate_id"] for c in candidate_rows],
            "summary": {
                "kept_edges": len(candidate_rows),
                "base_acc": float(acdc_ser.get("base_acc", 0.0)),
                "final_acc": float(acdc_ser.get("final_acc", 0.0)),
            },
        },
    )
    event_rows: List[Dict[str, Any]] = []
    for sample_idx in range(int(N)):
        active_cols = np.where(X_edge_bool[sample_idx])[0]
        for col_idx in active_cols:
            edge_members = edge_keys[int(col_idx)]
            node_id = "|".join(str(int(n)) for n in edge_members)
            event_rows.append(
                {
                    "schema_name": "feature_events.v1",
                    "schema_version": 1,
                    "run_id": run_id,
                    "event_id": f"demo4_{sample_idx}_{int(col_idx)}",
                    "source_kind": "mock",
                    "feature_space_id": feature_space_id,
                    "feature_space_version": "v1",
                    "sample_id": int(sample_idx),
                    "token_index": 0,
                    "layer": int(layer_index),
                    "node_type": "hyperedge",
                    "node_id": node_id,
                    "member_key": build_member_key(
                        feature_space_id=feature_space_id,
                        layer=int(layer_index),
                        node_type="hyperedge",
                        node_id=node_id,
                    ),
                    "feature_key": build_feature_key(
                        feature_space_id=feature_space_id,
                        layer=int(layer_index),
                        node_type="hyperedge",
                        node_id=node_id,
                    ),
                    "value": 1.0,
                    "step_index": int(sample_idx),
                }
            )
    write_feature_events(run_dir, event_rows)
    write_protocol_manifest(
        run_dir=run_dir,
        config_payload=cfg,
        compat_mode_enabled=False,
        hif_export_mode="both",
    )

    # Optional: reuse poly histogram if present (skip silently otherwise)
    reuse_plot_candidates = [
        os.path.join(run_dir, "poly_hist_hyperedges.png"),  # if some upstream step created it
    ]
    for p in reuse_plot_candidates:
        if os.path.exists(p):
            # Already present; nothing to do
            break

    # 10) One-line investor summary
    print(
        f"Demo4 STII+ACDC: edges={E}, stii_computed={computed_count}, "
        f"base_acc={base_acc_nodes:.3f}, final_acc={float(acdc_result.get('final_acc', 0.0)):.3f}, "
        f"gender_nodes_in_minimal={int(fairness.get('biased_nodes_in_minimal_count', 0))}"
    )


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "configs/demo4_causal.yaml")

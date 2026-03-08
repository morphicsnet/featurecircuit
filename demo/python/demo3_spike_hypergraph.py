from __future__ import annotations

import os
import sys
import json
import random
from typing import Any, Dict, List, Tuple

import numpy as np
import torch

# Make local modules importable (namespace package "python" at repo root)
sys.path.append(os.path.abspath("."))

from python.utils.config import load_yaml  # noqa: E402
from python.utils.artifacts import create_run_dir, dump_json, dump_yaml  # noqa: E402
from python.datasets.bank_sentences import generate_bank_dataset  # noqa: E402
from python.activations.extract import get_model_and_tokenizer, capture_layer_activations  # noqa: E402
from python.ensemble.intersection import build_pyensemble  # noqa: E402
from python.hypergraph.pipeline import build_hypergraph  # noqa: E402
from python.metrics.polysemanticity import (  # noqa: E402
    concept_probs,
    poly_count,
    entropy,
    summarize_polysemanticity,
)
from python.metrics.downstream import evaluate_logreg  # noqa: E402
from python.plots.hist import plot_histogram  # noqa: E402
from python.repro.protocol_manifest import (  # noqa: E402
    build_feature_key,
    build_member_key,
    build_relation_id,
    write_feature_events,
    write_feature_space,
    write_hif_exports,
    write_protocol_manifest,
    write_relations,
    write_structures,
)


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


def _metrics_bundle(prob: np.ndarray, eps: float, extra: Dict[str, Any]) -> Dict[str, Any]:
    """
    Produce a metrics dict with summary poly stats + extras.
    """
    summary = summarize_polysemanticity(prob, eps=eps)
    out = {
        **summary,
        **extra,
        "eps": eps,
    }
    return out


def main(config_path: str = "configs/demo3_spike_hypergraph.yaml") -> None:
    # Load config
    cfg = load_yaml(config_path)
    model_name: str = cfg["model_name"]
    layer_index: int = int(cfg["layer_index"])
    ds_cfg = cfg["dataset"]
    ens_cfg = cfg["ensemble"]
    spk_cfg = cfg["spike"]
    met_cfg = cfg["metrics"]
    out_cfg = cfg["outputs"]

    # Determinism: prefer dataset seed for global sampling unless otherwise specified
    global_seed = int(ds_cfg.get("seed", 1337))
    _seed_all(global_seed)

    # 1) Data
    n_per_class = int(ds_cfg["n_per_class"])
    texts, labels = generate_bank_dataset(n_per_class=n_per_class, seed=global_seed)
    labels_np = np.asarray(labels, dtype=np.int32)
    num_concepts = int(len(set(labels)))
    concept_names = ds_cfg.get("concepts", [f"concept_{i}" for i in range(num_concepts)])

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

    # 4) Hypergraph pipeline (spikes + GSE + aggregation)
    t_start = float(spk_cfg["t_start"])
    delta_t = float(spk_cfg["delta_t"])
    min_sigmoid = float(spk_cfg["min_sigmoid"])
    gse_window = float(spk_cfg["gse_window"])

    _store, features_bool, edge_keys, edge_counts = build_hypergraph(
        ensemble=ensemble,
        acts=acts,
        labels=labels_np,
        t_start=t_start,
        delta_t=delta_t,
        min_sigmoid=min_sigmoid,
        gse_window=gse_window,
    )
    N, E = int(features_bool.shape[0]), int(features_bool.shape[1])

    # 5) Metrics on hyperedge features
    eps = float(met_cfg["eps"])
    active_threshold_hyperedge = float(met_cfg["active_threshold_hyperedge"])
    bins = int(met_cfg["hist_bins"])

    features_float = features_bool.astype(np.float32)
    if E == 0:
        # Graceful path: no hyperedges formed
        base_dir = out_cfg["base_dir"]
        run_tag = out_cfg.get("run_tag", None)
        run_dir = create_run_dir(base_dir=base_dir, run_tag=run_tag)

        # Save minimal artifacts
        np.save(os.path.join(run_dir, "features_hyperedges.npy"), features_bool)
        dump_yaml(cfg, os.path.join(run_dir, "config.yaml"))
        with open(os.path.join(run_dir, "edge_keys.json"), "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)
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
            "feature_space_id": "demo3.hyperedge_space",
            "relations": [],
        }

        metrics_h = {
            "representation": "hyperedges_spike_temporal",
            "num_features": 0,
            "num_concepts": int(num_concepts),
            "concepts": list(concept_names),
            "num_samples": int(N),
            "num_edges": 0,
            "edge_size_median": 0.0,
            "edge_size_p90": 0.0,
            "gse_window": gse_window,
            "spike": {"t_start": t_start, "delta_t": delta_t, "min_sigmoid": min_sigmoid},
            "thresholds": {
                "eps": eps,
                "active_threshold_hyperedge": active_threshold_hyperedge,
            },
            "accuracy": 0.0,
            "median_poly": 0.0,
            "p90_poly": 0.0,
            "monosemantic_rate": 0.0,
            "note": "No hyperedges formed; check gse_window/min_sigmoid/top_k.",
        }
        dump_json(metrics_h, os.path.join(run_dir, "metrics_hyperedges.json"))
        write_feature_space(
            run_dir,
            {
                "schema_name": "feature_space.v1",
                "schema_version": 1,
                "feature_space_id": "demo3.hyperedge_space",
                "feature_space_type": "hyperedge",
                "producer": "demo3_spike_hypergraph",
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
        write_hif_exports(run_dir, structures_payload)
        write_feature_events(run_dir, [])
        write_protocol_manifest(
            run_dir=run_dir,
            config_payload=cfg,
            compat_mode_enabled=False,
            hif_export_mode="both",
        )
        print("Demo3 hypergraph: no hyperedges formed; exported empty HIF and minimal artifacts.")
        return

    prob_h = concept_probs(
        features_float,
        labels_np,
        num_concepts=num_concepts,
        active_threshold=active_threshold_hyperedge,
    )  # [E, m]
    poly_h = poly_count(prob_h, eps=eps)  # [E]
    ent_h = entropy(prob_h)  # [E]
    acc_h = evaluate_logreg(features_float, labels_np, seed=global_seed)["accuracy"]

    # Edge size summary
    edge_sizes = np.asarray([len(k) for k in edge_keys], dtype=np.int32)
    edge_size_median = float(np.median(edge_sizes)) if len(edge_sizes) > 0 else 0.0
    edge_size_p90 = float(np.percentile(edge_sizes, 90.0)) if len(edge_sizes) > 0 else 0.0

    metrics_h: Dict[str, Any] = _metrics_bundle(
        prob_h,
        eps=eps,
        extra={
            "representation": "hyperedges_spike_temporal",
            "num_features": int(prob_h.shape[0]),
            "num_concepts": int(prob_h.shape[1]),
            "concepts": list(concept_names),
            "num_samples": int(N),
            "num_edges": int(E),
            "edge_size_median": edge_size_median,
            "edge_size_p90": edge_size_p90,
            "gse_window": gse_window,
            "spike": {"t_start": t_start, "delta_t": delta_t, "min_sigmoid": min_sigmoid},
            "thresholds": {
                "eps": eps,
                "active_threshold_hyperedge": active_threshold_hyperedge,
            },
            "accuracy": float(acc_h),
        },
    )

    # 6) Artifacts
    base_dir = out_cfg["base_dir"]
    run_tag = out_cfg.get("run_tag", None)
    run_dir = create_run_dir(base_dir=base_dir, run_tag=run_tag)

    # Save arrays and configs
    np.save(os.path.join(run_dir, "features_hyperedges.npy"), features_bool)
    with open(os.path.join(run_dir, "edge_keys.json"), "w", encoding="utf-8") as f:
        json.dump([list(map(int, t)) for t in edge_keys], f, indent=2)
    dump_yaml(cfg, os.path.join(run_dir, "config.yaml"))
    dump_json(metrics_h, os.path.join(run_dir, "metrics_hyperedges.json"))

    run_id = os.path.basename(os.path.abspath(run_dir))
    feature_space_id = "demo3.hyperedge_space"
    relation_builder_type = "temporal_coactivation"
    relation_builder_version = "v1"
    structures = []
    relations = []
    for idx, ek in enumerate(edge_keys):
        members = [str(int(x)) for x in ek]
        support_count = int(edge_counts.get(ek, 0))
        structures.append(
            {
                "structure_id": f"struct_{idx}",
                "structure_type": "hyperedge",
                "members": members,
                "arity": len(members),
                "support_count": support_count,
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
            "producer": "demo3_spike_hypergraph",
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
    write_hif_exports(run_dir, structures_payload)

    # FeatureEventStream export (JSONL rows; one active hyperedge event per sample).
    event_rows: List[Dict[str, Any]] = []
    for sample_idx in range(N):
        active_cols = np.where(features_bool[sample_idx])[0]
        for col_idx in active_cols:
            members = edge_keys[int(col_idx)]
            node_id = "|".join(str(int(n)) for n in members)
            event_rows.append(
                {
                    "schema_name": "feature_events.v1",
                    "schema_version": 1,
                    "run_id": run_id,
                    "event_id": f"demo3_{sample_idx}_{int(col_idx)}",
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

    # Plot
    title_h = (
        f"Spike-temporal Hyperedge polysemanticity (eps={eps:.2g}) — "
        f"median={metrics_h['median_poly']:.2f}, mono={metrics_h['monosemantic_rate']:.1%}"
    )
    plot_histogram(poly_h, bins=bins, title=title_h, path=os.path.join(run_dir, "poly_hist_hyperedges.png"))

    write_protocol_manifest(
        run_dir=run_dir,
        config_payload=cfg,
        compat_mode_enabled=False,
        hif_export_mode="both",
    )

    # One-line investor summary
    print(
        "Demo3 hypergraph: "
        f"hyperedge poly median={metrics_h['median_poly']:.2f}, "
        f"monosemantic_rate={metrics_h['monosemantic_rate']:.3f}, "
        f"accuracy={metrics_h['accuracy']:.3f}, edges={E}"
    )


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "configs/demo3_spike_hypergraph.yaml")

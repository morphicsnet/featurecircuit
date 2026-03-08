from __future__ import annotations

import os
import sys
from typing import Any, Iterable


def _ensure_protocol_path() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(here, "..", "..", ".."))
    protocol_py = os.path.join(repo_root, "core", "protocol", "python")
    if protocol_py not in sys.path:
        sys.path.append(protocol_py)


def _package_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    try:
        import importlib.metadata as ilm

        for pkg in ("py_nsi", "numpy", "scikit-learn"):
            try:
                versions[pkg] = ilm.version(pkg)
            except Exception:
                versions[pkg] = "unknown"
    except Exception:
        versions = {"py_nsi": "unknown", "numpy": "unknown", "scikit-learn": "unknown"}
    return versions


def _extract_runtime_metadata(config_payload: dict[str, Any]) -> dict[str, Any]:
    cfg = config_payload if isinstance(config_payload, dict) else {}
    dataset_cfg = cfg.get("dataset", {}) if isinstance(cfg.get("dataset"), dict) else {}
    ensemble_cfg = cfg.get("ensemble", {}) if isinstance(cfg.get("ensemble"), dict) else {}
    spike_cfg = cfg.get("spike", {}) if isinstance(cfg.get("spike"), dict) else {}
    model_id = (
        cfg.get("model_name")
        or cfg.get("model", {}).get("hf_model")
        or cfg.get("model", {}).get("model_id")
    )
    return {
        "model_identifier": model_id or "unknown",
        "layer_selection": cfg.get("layer_index"),
        "dataset_provenance": dataset_cfg.get("name") or dataset_cfg.get("source"),
        "random_seeds": {
            "dataset_seed": dataset_cfg.get("seed"),
            "ensemble_seeds": ensemble_cfg.get("seeds"),
            "sae_seed": (cfg.get("sae") or {}).get("seed") if isinstance(cfg.get("sae"), dict) else None,
        },
        "batching_parameters": {
            "n_samples": dataset_cfg.get("n_samples"),
            "n_per_class": dataset_cfg.get("n_per_class"),
            "batch_size": (cfg.get("model") or {}).get("batch_size") if isinstance(cfg.get("model"), dict) else None,
        },
        "activation_extraction_points": {
            "layer": cfg.get("layer_index"),
            "kind": (cfg.get("model") or {}).get("activation_kind") if isinstance(cfg.get("model"), dict) else None,
        },
        "spike_parameters": spike_cfg,
    }


def write_protocol_manifest(
    run_dir: str,
    config_payload: dict[str, Any],
    compat_mode_enabled: bool,
    hif_export_mode: str,
    runtime_metadata: dict[str, Any] | None = None,
) -> str:
    _ensure_protocol_path()
    from featurecircuit_protocol.artifacts import ProtocolManifest
    from featurecircuit_protocol.io import config_checksum, write_json
    from featurecircuit_protocol.validation import validate_payload

    run_id = os.path.basename(os.path.abspath(run_dir))
    manifest = ProtocolManifest(
        protocol_version="featurecircuit-protocol.v1",
        run_id=run_id,
        artifact_schema_versions={
            "feature_space": "feature_space.v1",
            "feature_events": "feature_events.v1",
            "relations": "relations.v1",
            "structures": "structures.v1",
            "candidates": "candidates.v1",
            "scores": "scores.v1",
            "hif": "hif.v0",
            "hif_legacy_demo": "hif_legacy_demo.v0",
            "protocol_manifest": "protocol_manifest.v1",
        },
        package_versions=_package_versions(),
        compat_mode_enabled=bool(compat_mode_enabled),
        hif_export_mode=hif_export_mode,
        run_config_checksum=config_checksum(config_payload),
        metadata={
            "runner": "demo",
            **_extract_runtime_metadata(config_payload),
            **(runtime_metadata or {}),
        },
    ).to_dict()

    validate_payload(manifest, "protocol_manifest.v1.json")
    out = os.path.join(run_dir, "protocol_manifest.v1.json")
    write_json(out, manifest)
    return out


def write_feature_events(run_dir: str, rows: Iterable[dict[str, Any]]) -> str:
    _ensure_protocol_path()
    from featurecircuit_protocol.io import write_jsonl
    from featurecircuit_protocol.validation import validate_jsonl_file

    out = os.path.join(run_dir, "feature_events.v1.jsonl")
    write_jsonl(out, rows)
    validate_jsonl_file(out, "feature_events.v1.jsonl")
    return out


def write_feature_space(run_dir: str, payload: dict[str, Any]) -> str:
    _ensure_protocol_path()
    from featurecircuit_protocol.io import write_json
    from featurecircuit_protocol.validation import validate_payload

    validate_payload(payload, "feature_space.v1.json")
    out = os.path.join(run_dir, "feature_space.v1.json")
    write_json(out, payload)
    return out


def write_relations(run_dir: str, payload: dict[str, Any]) -> str:
    _ensure_protocol_path()
    from featurecircuit_protocol.io import write_json
    from featurecircuit_protocol.validation import validate_payload

    validate_payload(payload, "relations.v1.json")
    out = os.path.join(run_dir, "relations.v1.json")
    write_json(out, payload)
    return out


def write_structures(run_dir: str, payload: dict[str, Any]) -> str:
    _ensure_protocol_path()
    from featurecircuit_protocol.io import write_json
    from featurecircuit_protocol.validation import validate_payload

    validate_payload(payload, "structures.v1.json")
    out = os.path.join(run_dir, "structures.v1.json")
    write_json(out, payload)
    return out


def write_hif_exports(run_dir: str, structure_artifact_payload: dict[str, Any]) -> tuple[str, str]:
    _ensure_protocol_path()
    from featurecircuit_protocol.exports import structure_to_hif_legacy_demo, structure_to_hif_v0
    from featurecircuit_protocol.io import write_json
    from featurecircuit_protocol.validation import validate_payload

    canonical = structure_to_hif_v0(structure_artifact_payload)
    legacy = structure_to_hif_legacy_demo(structure_artifact_payload)
    validate_payload(canonical, "hif.v0.json")
    validate_payload(legacy, "hif_legacy_demo.v0.json")
    canonical_out = os.path.join(run_dir, "hypergraph.hif.v0.json")
    legacy_out = os.path.join(run_dir, "hypergraph.hif.json")
    write_json(canonical_out, canonical)
    write_json(legacy_out, legacy)
    return canonical_out, legacy_out


def write_candidates(run_dir: str, payload: dict[str, Any]) -> str:
    _ensure_protocol_path()
    from featurecircuit_protocol.io import write_json
    from featurecircuit_protocol.validation import validate_payload

    validate_payload(payload, "candidates.v1.json")
    out = os.path.join(run_dir, "candidates.v1.json")
    write_json(out, payload)
    return out


def write_scores(run_dir: str, payload: dict[str, Any]) -> str:
    _ensure_protocol_path()
    from featurecircuit_protocol.io import write_json
    from featurecircuit_protocol.validation import validate_payload

    validate_payload(payload, "scores.v1.json")
    out = os.path.join(run_dir, "scores.v1.json")
    write_json(out, payload)
    return out


def build_member_key(feature_space_id: str, layer: int, node_type: str, node_id: str | int) -> str:
    _ensure_protocol_path()
    from featurecircuit_protocol.ids import member_key

    return member_key(feature_space_id=feature_space_id, layer=layer, node_type=node_type, node_id=node_id)


def build_feature_key(feature_space_id: str, layer: int, node_type: str, node_id: str | int) -> str:
    _ensure_protocol_path()
    from featurecircuit_protocol.ids import feature_key

    return feature_key(feature_space_id=feature_space_id, layer=layer, node_type=node_type, node_id=node_id)


def build_relation_id(
    relation_builder_type: str,
    relation_builder_version: str,
    member_feature_ids_ordered: list[str],
    directionality: str,
    arity: int,
    construction_rule: str,
    threshold: float | None,
) -> str:
    _ensure_protocol_path()
    from featurecircuit_protocol.ids import relation_id

    return relation_id(
        relation_builder_type=relation_builder_type,
        relation_builder_version=relation_builder_version,
        member_feature_ids_ordered=member_feature_ids_ordered,
        directionality=directionality,
        arity=arity,
        construction_rule=construction_rule,
        threshold=threshold,
    )


def build_candidate_id(
    structure_builder_type: str,
    structure_builder_version: str,
    member_feature_ids: list[str],
    candidate_type: str,
    arity: int,
) -> str:
    _ensure_protocol_path()
    from featurecircuit_protocol.ids import candidate_id

    return candidate_id(
        structure_builder_type=structure_builder_type,
        structure_builder_version=structure_builder_version,
        member_feature_ids=member_feature_ids,
        candidate_type=candidate_type,
        arity=arity,
    )

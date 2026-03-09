from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable, Sequence


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256(payload: Any) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def member_key(feature_space_id: str, layer: int, node_type: str, node_id: str | int) -> str:
    return f"{feature_space_id}:{int(layer)}:{node_type}:{node_id}"


def feature_key(feature_space_id: str, layer: int, node_type: str, node_id: str | int) -> str:
    return member_key(feature_space_id=feature_space_id, layer=layer, node_type=node_type, node_id=node_id)


def feature_id(feature_space_id: str, layer: int, node_type: str, node_id: str | int) -> str:
    payload = {
        "feature_space_id": feature_space_id,
        "layer": int(layer),
        "node_type": str(node_type),
        "node_id": str(node_id),
    }
    return f"f_{_sha256(payload)[:16]}"


def relation_id(
    relation_builder_type: str,
    relation_builder_version: str,
    member_feature_ids_ordered: Sequence[str],
    directionality: str,
    arity: int,
    construction_rule: str,
    threshold: float | None,
) -> str:
    payload = {
        "relation_builder_type": relation_builder_type,
        "relation_builder_version": relation_builder_version,
        "members": list(member_feature_ids_ordered),
        "directionality": directionality,
        "arity": int(arity),
        "construction_rule": construction_rule,
        "threshold": threshold,
    }
    return f"r_{_sha256(payload)[:16]}"


def candidate_id(
    structure_builder_type: str,
    structure_builder_version: str,
    member_feature_ids: Iterable[str],
    candidate_type: str,
    arity: int,
) -> str:
    payload = {
        "structure_builder_type": structure_builder_type,
        "structure_builder_version": structure_builder_version,
        "members": sorted(str(m) for m in member_feature_ids),
        "candidate_type": candidate_type,
        "arity": int(arity),
    }
    return f"c_{_sha256(payload)[:16]}"


def structure_id(
    structure_builder_type: str,
    structure_builder_version: str,
    members: Iterable[str],
    structure_type: str,
) -> str:
    payload = {
        "structure_builder_type": structure_builder_type,
        "structure_builder_version": structure_builder_version,
        "members": sorted(str(m) for m in members),
        "structure_type": structure_type,
    }
    return f"s_{_sha256(payload)[:16]}"


def snapshot_id(
    training_run_id: str,
    checkpoint_id: str,
    feature_space_id: str,
    candidate_set_id: str,
) -> str:
    payload = {
        "training_run_id": training_run_id,
        "checkpoint_id": checkpoint_id,
        "feature_space_id": feature_space_id,
        "candidate_set_id": candidate_set_id,
    }
    return f"snap_{_sha256(payload)[:16]}"

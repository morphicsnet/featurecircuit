from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ActivationBatch:
    activation_batch_id: str
    run_id: str
    training_run_id: str
    checkpoint_id: str
    batch_id: str
    model_id: str
    model_revision: str
    tokenizer_id: str
    layer_targets: list[int]
    activation_kind: str
    shape_summary: dict[str, Any]
    dtype: str
    device: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_name": "activation_batch.v1",
            "schema_version": 1,
            **asdict(self),
        }


@dataclass
class FeatureSpaceDescriptor:
    feature_space_id: str
    feature_space_type: str
    producer: str
    producer_version: str
    model_id: str
    layer_map: dict[str, Any]
    dim: int
    activation_rule: str
    checksum: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_name": "feature_space.v1",
            "schema_version": 1,
            **asdict(self),
        }


@dataclass
class FeatureEvent:
    run_id: str
    event_id: str
    source_kind: str
    feature_space_id: str
    feature_space_version: str
    sample_id: str | int
    token_index: int
    layer: int
    node_type: str
    node_id: str | int
    value: float
    step_index: int
    sequence_id: str | int | None = None
    doc_id: str | int | None = None
    timestamp: str | None = None
    dictionary_id: str | None = None
    dictionary_version: str | None = None
    dictionary_type: str | None = None
    feature_origin_layer: int | None = None
    member_key: str | None = None
    feature_key: str | None = None
    candidate_key: str | None = None
    task_family: str | None = None
    prompt_family: str | None = None
    split: str | None = None
    label: str | None = None
    capability_tag: str | None = None
    safety_tag: str | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        out = {
            "schema_name": "feature_events.v1",
            "schema_version": 1,
            **asdict(self),
        }
        return {k: v for k, v in out.items() if v is not None}


@dataclass
class FeatureEventStream:
    run_id: str
    source_kind: str
    feature_space_id: str
    feature_space_version: str
    events: list[FeatureEvent]

    def to_jsonl_rows(self) -> list[dict[str, Any]]:
        rows = []
        for e in self.events:
            d = e.to_dict()
            d.setdefault("run_id", self.run_id)
            d.setdefault("source_kind", self.source_kind)
            d.setdefault("feature_space_id", self.feature_space_id)
            d.setdefault("feature_space_version", self.feature_space_version)
            rows.append(d)
        return rows


@dataclass
class RelationArtifact:
    run_id: str
    relation_builder_type: str
    relation_builder_version: str
    feature_space_id: str
    relations: list[dict[str, Any]]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_name": "relations.v1",
            "schema_version": 1,
            "run_id": self.run_id,
            "relation_builder_type": self.relation_builder_type,
            "relation_builder_version": self.relation_builder_version,
            "feature_space_id": self.feature_space_id,
            "relations": self.relations,
            "metadata": self.metadata,
        }


@dataclass
class StructureArtifact:
    run_id: str
    structure_builder_type: str
    structure_builder_version: str
    structures: list[dict[str, Any]]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_name": "structures.v1",
            "schema_version": 1,
            "run_id": self.run_id,
            "structure_builder_type": self.structure_builder_type,
            "structure_builder_version": self.structure_builder_version,
            "structures": self.structures,
            "metadata": self.metadata,
        }


@dataclass
class CandidateSetArtifact:
    run_id: str
    candidates: list[dict[str, Any]]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_name": "candidates.v1",
            "schema_version": 1,
            "run_id": self.run_id,
            "candidates": self.candidates,
            "metadata": self.metadata,
        }


@dataclass
class CircuitSnapshotArtifact:
    snapshot_id: str
    run_id: str
    training_run_id: str
    checkpoint_id: str
    feature_space_id: str
    relation_artifact_id: str
    structure_artifact_id: str
    candidate_set_id: str
    candidate_ids: list[str]
    summary: dict[str, Any]
    parent_snapshot_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        out = {
            "schema_name": "circuit_snapshot.v1",
            "schema_version": 1,
            **asdict(self),
        }
        return {k: v for k, v in out.items() if v is not None}


@dataclass
class ScoreBundleArtifact:
    run_id: str
    scores: list[dict[str, Any]]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_name": "scores.v1",
            "schema_version": 1,
            "run_id": self.run_id,
            "scores": self.scores,
            "metadata": self.metadata,
        }


@dataclass
class ProtocolManifest:
    protocol_version: str
    run_id: str
    artifact_schema_versions: dict[str, str]
    package_versions: dict[str, str]
    compat_mode_enabled: bool
    hif_export_mode: str
    run_config_checksum: str
    export_profiles: list[str]
    lineage: dict[str, Any]
    model_info: dict[str, Any] = field(default_factory=dict)
    feature_space_descriptors: list[str] = field(default_factory=list)
    relation_builders: list[str] = field(default_factory=list)
    structure_builders: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        out = {
            "schema_name": "protocol_manifest.v1",
            "schema_version": 1,
            **asdict(self),
        }
        return out

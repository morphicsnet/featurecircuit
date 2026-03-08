"""FeatureCircuit Protocol reference artifacts and helpers."""

from .artifacts import (
    FeatureSpaceDescriptor,
    FeatureEvent,
    FeatureEventStream,
    RelationArtifact,
    StructureArtifact,
    CandidateSetArtifact,
    ScoreBundleArtifact,
    ProtocolManifest,
)
from .ids import (
    feature_id,
    relation_id,
    candidate_id,
    member_key,
    feature_key,
)
from .io import write_json, write_jsonl, read_json
from .validation import validate_payload, validate_json_file, validate_jsonl_file
from .compatibility import CompatibilityError, check_stage_compatibility, assert_stage_compatible

__all__ = [
    "FeatureSpaceDescriptor",
    "FeatureEvent",
    "FeatureEventStream",
    "RelationArtifact",
    "StructureArtifact",
    "CandidateSetArtifact",
    "ScoreBundleArtifact",
    "ProtocolManifest",
    "feature_id",
    "relation_id",
    "candidate_id",
    "member_key",
    "feature_key",
    "write_json",
    "write_jsonl",
    "read_json",
    "validate_payload",
    "validate_json_file",
    "validate_jsonl_file",
    "CompatibilityError",
    "check_stage_compatibility",
    "assert_stage_compatible",
]

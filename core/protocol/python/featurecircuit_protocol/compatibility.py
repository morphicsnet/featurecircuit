from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


class CompatibilityError(ValueError):
    """Raised when artifact-level compatibility checks fail."""


def check_stage_compatibility(
    *,
    protocol_manifest: Mapping[str, Any],
    required_schema_versions: Mapping[str, str] | None = None,
    feature_space: Mapping[str, Any] | None = None,
    expected_feature_space_id: str | None = None,
    expected_model_id: str | None = None,
    expected_layers: Sequence[int] | None = None,
    candidate_set: Mapping[str, Any] | None = None,
    max_candidate_arity: int | None = None,
    score_bundle: Mapping[str, Any] | None = None,
    required_score_fields: Sequence[str] | None = None,
) -> list[str]:
    errors: list[str] = []

    artifact_versions = protocol_manifest.get("artifact_schema_versions")
    if not isinstance(artifact_versions, Mapping):
        errors.append("protocol_manifest.artifact_schema_versions is missing or invalid")
    else:
        for name, required in (required_schema_versions or {}).items():
            got = artifact_versions.get(name)
            if got != required:
                errors.append(f"schema version mismatch for {name}: expected {required}, got {got}")

    if feature_space is not None:
        if expected_feature_space_id is not None and feature_space.get("feature_space_id") != expected_feature_space_id:
            errors.append(
                "feature_space_id mismatch: "
                f"expected {expected_feature_space_id}, got {feature_space.get('feature_space_id')}"
            )
        if expected_model_id is not None and feature_space.get("model_id") != expected_model_id:
            errors.append(
                f"model_id mismatch: expected {expected_model_id}, got {feature_space.get('model_id')}"
            )
        if expected_layers:
            layer_map = feature_space.get("layer_map")
            if not isinstance(layer_map, Mapping):
                errors.append("feature_space.layer_map is missing or invalid")
            else:
                got_layers = {int(k) for k in layer_map.keys()}
                missing = sorted(set(int(x) for x in expected_layers) - got_layers)
                if missing:
                    errors.append(f"layer compatibility failure: missing layers {missing}")

    if candidate_set is not None and max_candidate_arity is not None:
        rows = candidate_set.get("candidates")
        if not isinstance(rows, list):
            errors.append("candidate_set.candidates is missing or invalid")
        else:
            over = [int(r.get("arity", -1)) for r in rows if int(r.get("arity", -1)) > int(max_candidate_arity)]
            if over:
                errors.append(
                    "candidate arity unsupported: "
                    f"max supported {int(max_candidate_arity)}, found {sorted(set(over))}"
                )

    if score_bundle is not None and required_score_fields:
        rows = score_bundle.get("scores")
        if not isinstance(rows, list):
            errors.append("score_bundle.scores is missing or invalid")
        else:
            for idx, row in enumerate(rows):
                if not isinstance(row, Mapping):
                    errors.append(f"score row {idx} is invalid")
                    continue
                missing = [name for name in required_score_fields if name not in row]
                if missing:
                    errors.append(f"score row {idx} missing required fields: {missing}")

    return errors


def assert_stage_compatible(**kwargs: Any) -> None:
    errors = check_stage_compatibility(**kwargs)
    if errors:
        raise CompatibilityError("; ".join(errors))


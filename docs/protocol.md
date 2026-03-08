# Protocol Contracts

## Artifact Schemas
- `feature_space.v1.json`
- `feature_events.v1.jsonl`
- `relations.v1.json`
- `structures.v1.json`
- `candidates.v1.json`
- `scores.v1.json`
- `hif.v0.json`
- `hif_legacy_demo.v0.json`
- `protocol_manifest.v1.json`

All schemas are located in `core/protocol/schemas/`.

## Stable Identity Rules
Canonical helper implementations live in `core/protocol/python/featurecircuit_protocol/ids.py`.

### Feature IDs
Deterministic hash over:
- `feature_space_id`
- `layer`
- `node_type`
- `node_id`

### Relation IDs
Deterministic hash over:
- `relation_builder_type`
- `relation_builder_version`
- ordered member feature IDs
- `directionality`
- `arity`
- construction rule and threshold fields

### Candidate IDs
Deterministic hash over:
- `structure_builder_type`
- `structure_builder_version`
- sorted member feature IDs
- `candidate_type`
- `arity`

### Event Keys
- `member_key = "{feature_space_id}:{layer}:{node_type}:{node_id}"`
- `feature_key` aliases `member_key` in v1.

## Manifest Contract
Each run emits `protocol_manifest.v1.json` with:
- protocol version
- artifact schema versions
- package versions
- compat mode flag
- HIF export mode
- run config checksum

Compatibility checks for downstream stages are implemented in:
- `core/protocol/python/featurecircuit_protocol/compatibility.py`

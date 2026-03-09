# Protocol Contracts

## Artifact Schemas
- `activation_batch.v1.json`
- `feature_space.v1.json`
- `feature_events.v1.jsonl`
- `relations.v1.json`
- `structures.v1.json`
- `candidates.v1.json`
- `circuit_snapshot.v1.json`
- `scores.v1.json`
- `hif.v0.json`
- `hif_legacy_demo.v0.json`
- `protocol_manifest.v1.json`

All schemas are located in `core/protocol/schemas/`.

## Naming and Envelope Convention
- Protocol-native artifacts use `schema_name` + `schema_version`.
- Protocol-native artifacts include a top-level `metadata` envelope for extensible provenance fields.
- Deterministic IDs for features/relations/structures/candidates/snapshots are generated only via `featurecircuit_protocol.ids`.

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

### Structure IDs
Deterministic hash over:
- `structure_builder_type`
- `structure_builder_version`
- sorted member feature IDs
- `structure_type`

### Snapshot IDs
Deterministic hash over:
- `training_run_id`
- `checkpoint_id`
- `feature_space_id`
- `candidate_set_id`

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
- export profile declarations
- lineage section (`run_id`, `training_run_id`, `checkpoint_id`)

Compatibility checks for downstream stages are implemented in:
- `core/protocol/python/featurecircuit_protocol/compatibility.py`

## Tooling
- Schema validator CLI: `tools/schema_validate/main.py`
- Artifact diff CLI: `tools/artifact_diff/main.py`

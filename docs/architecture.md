# FeatureCircuit Protocol Architecture

## Boundary Rule
Protocol layer owns schemas, identifiers, artifact contracts, and deterministic serialization.
Implementation layer owns concrete Rust/Python logic, builders, and reproducibility flows.

## Top-Level Layout
- `core/`: protocol contracts and core implementation
- `demo/`: reproducibility workflows and notebooks
- `satellites/`: modules that depend only on public interfaces and protocol schemas

## Protocol vs Implementation
### Protocol
- Schema files in `core/protocol/schemas/`
- Stable ID rules in `core/protocol/python/featurecircuit_protocol/ids.py`
- Artifact and manifest contracts in `core/protocol/python/featurecircuit_protocol/artifacts.py`

### Implementation
- Rust core in `core/nsi_core/`
- Python bindings in `core/py_nsi/`
- Demo pipelines in `demo/python/`

## Integration Boundary
Downstream systems (Hypercircuit, Sidecar, other consumers) consume emitted artifacts (`feature_events`, `candidates`, `scores`) and do not import internal in-memory structures.

## Canonical Artifact Chain
`ActivationBatch` -> `FeatureSpaceDescriptor` -> `FeatureEventStream` -> `RelationArtifact` -> `StructureArtifact` -> `CandidateSetArtifact` -> `CircuitSnapshotArtifact` -> `ScoreBundleArtifact` -> exporter profiles.

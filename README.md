# FeatureCircuit Protocol

FeatureCircuit Protocol is the canonical research-protocol repository for feature spaces, relation artifacts, structure construction, and reproducible circuit-analysis outputs.

## Repository Faces
- `core/`: protocol contracts, stable identifiers, Rust core (`nsi_core`), Python bindings (`py_nsi`)
- `demo/`: reproducibility corridor (scripts, notebooks, configs, docs, example fixtures)
- `satellites/`: out-of-scope companion modules (`nsi-client`, `nsi-engine`)
- `legacy/`: imported historical trees from previous repos

## Quickstart
### Core + bindings
```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip maturin pytest jsonschema pyyaml numpy
maturin develop --release -m core/py_nsi/Cargo.toml
python -c "import py_nsi; print('py_nsi OK')"
```

### Demo corridor
```bash
cd demo
python python/demo1_baseline.py
python python/demo2_ensemble.py
python python/demo3_spike_hypergraph.py
python python/demo4_causal.py
python python/demo5_dashboard.py
```

Runtime artifacts are emitted under `runs/` by default.

## Canonical Protocol Chain
```text
ActivationBatch
  -> FeatureSpaceDescriptor
  -> FeatureEventStream
  -> RelationArtifact
  -> StructureArtifact
  -> CandidateSetArtifact
  -> ScoreBundleArtifact
  -> HIF Export / Report Artifact
```

## API and Compatibility
- Canonical Python API surface: solver-style `py_nsi` classes.
- Legacy demo API is available only via `py_nsi.compat`.
- Compatibility window: one consolidation release.

## Migration Matrix
| Old repo/path/API | New location | Status |
| --- | --- | --- |
| `superposition-demo/...` | `featurecircuit-protocol/demo/...` | migrated |
| `superposition-solver1/nsi_core` | `featurecircuit-protocol/core/nsi_core` | canonical |
| `superposition-solver1/py_nsi` | `featurecircuit-protocol/core/py_nsi` | canonical |
| old demo `py_nsi` names | `py_nsi.compat...` | deprecated |
| solver-style API names | `py_nsi...` | canonical |
| `superposition-solver1/nsi-client` | `featurecircuit-protocol/satellites/nsi-client` | satellite |
| `superposition-solver1/nsi-engine` | `featurecircuit-protocol/satellites/nsi-engine` | satellite |

## Documentation
- Protocol architecture: `docs/architecture.md`
- Protocol contracts and IDs: `docs/protocol.md`
- Consolidation migration runbook: `docs/migration.md`
- Release guide: `docs/release.md`
- Release checklist: `RELEASE_CHECKLIST.md`
- Demo docs index: `demo/docs/`

## CI and Testing
- Rust core and bindings tests: `cargo test --workspace`
- Python tests: `pytest -q tests`
- Contract/schema validation is part of Python tests.

## Release
Run preflight from repo root:

```bash
scripts/release_preflight.sh
```

Optional heavier gate (smoke corridor + artifact build):

```bash
scripts/release_preflight.sh --with-smoke --build-artifacts
```

Verify built wheel in a clean temporary venv:

```bash
scripts/release_verify_artifacts.sh
```

Check release blockers before tagging:

```bash
scripts/release_blockers.sh --version 0.1.0
```

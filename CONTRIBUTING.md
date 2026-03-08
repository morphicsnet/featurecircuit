# Contributing to FeatureCircuit Protocol

## Repo Faces
- `core/`: protocol contracts and stable public runtime APIs.
- `demo/`: reproducible experiment corridor.
- `satellites/`: out-of-scope companion modules.

## Rules
- Keep protocol schema changes versioned and backward-safe.
- Do not add new internal dependencies from `satellites/` to `core/*/src` internals.
- Prefer canonical `py_nsi` API in internal code; `py_nsi.compat` is external-only and temporary.

## Dev Setup
```bash
uv venv .venv --python 3.12 --seed --clear
.venv/bin/pip install maturin pytest jsonschema pyyaml numpy
TMPDIR="$PWD/.tmp" .venv/bin/maturin develop --release -m core/py_nsi/Cargo.toml
```

## Validation
```bash
cargo test --workspace
PYTHONPATH="core/protocol/python:demo" .venv/bin/pytest -q tests
```

# featurecircuit Core
> Protocol contracts, stable identifiers, and public runtime primitives for the featurecircuit stack.

The `core/` face owns the things other tools should be able to trust: schemas, deterministic IDs, public crate surfaces, and the canonical Python bindings.

## Fastest path
```bash
maturin develop --release -m core/py_nsi/Cargo.toml
python -c "import py_nsi; print('py_nsi OK')"
```

## What lives here
- `nsi_core/`: Rust core crate and stable low-level runtime primitives
- `py_nsi/`: canonical Python bindings plus the temporary compat shim
- `protocol/`: schema files, ID rules, artifact contracts, and reference helpers

## Public surface
Depend on these surfaces:
- `nsi_core` public crate APIs
- `py_nsi` canonical classes
- schema files under `core/protocol/schemas/`
- protocol helpers under `core/protocol/python/featurecircuit_protocol/`

Do not depend on internal module paths inside implementation files.

## Go next
- Root guide: [featurecircuit](../README.md)
- Python bindings: [py_nsi README](py_nsi/README.md)
- Repro corridor: [demo README](../demo/README.md)

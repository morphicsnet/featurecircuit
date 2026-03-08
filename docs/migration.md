# Consolidation Migration Runbook

## Goal
Consolidate `superposition-demo` and `superposition-solver1` into `featurecircuit-protocol` without breaking first-release package identifiers (`nsi_core`, `py_nsi`).

## Path Migration
- core crates/bindings now live under `core/`
- demo scripts/configs/notebooks now live under `demo/`
- runtime outputs default to `runs/`

## Command Migration
### Before
```bash
maturin develop --release -m py_nsi/Cargo.toml
python python/demo1_baseline.py
```

### After
```bash
maturin develop --release -m core/py_nsi/Cargo.toml
cd demo
python python/demo1_baseline.py
```

## Compatibility Cutoff
- `py_nsi.compat` exists for one consolidation release only.
- New internal development must import canonical `py_nsi` classes.

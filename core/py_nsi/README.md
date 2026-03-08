# py_nsi

`py_nsi` provides Python bindings for `nsi_core` using PyO3.

## Build

```bash
maturin develop --release -m core/py_nsi/Cargo.toml
```

## Canonical API
- `SpikeEvent`
- `SpikeEncoder`
- `Island`
- `GraphStreamingEngine`
- `HypergraphStore`
- `EnsembleEncoder`

Temporary legacy shims remain under `py_nsi.compat` for one consolidation release.

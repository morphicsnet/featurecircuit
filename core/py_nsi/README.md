# py_nsi
> Python bindings for `nsi_core`, kept small on purpose so notebooks and scripts can touch the canonical runtime without dragging the whole repo around.

## Fastest path
```bash
maturin develop --release -m core/py_nsi/Cargo.toml
python -c "import py_nsi; print('py_nsi OK')"
```

## Canonical surface
- `SpikeEvent`
- `SpikeEncoder`
- `Island`
- `GraphStreamingEngine`
- `HypergraphStore`
- `EnsembleEncoder`

Temporary legacy shims remain under `py_nsi.compat` for the consolidation window only.

## When to use it
- Use `py_nsi` when you want the canonical binding surface from Python.
- Use the protocol helpers when you care about manifests, IDs, and schema validation.
- Use the demo corridor when you want a whole staged run, not just bound classes.

## Go next
- Core boundary: [core README](../README.md)
- Root guide: [featurecircuit](../../README.md)
- Demo corridor: [demo README](../../demo/README.md)

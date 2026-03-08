# Demo / Reproducibility Face

`demo/` is the reproducible research corridor.

## Layout
- `python/`: executable demo scripts and helper modules
- `configs/`: run configs (default runtime root `runs/`)
- `notebooks/`: notebook corridor
- `docs/`: architecture, metrics, and runbook docs
- `examples/outputs/`: fixture artifacts only

## Run
```bash
cd demo
python python/demo1_baseline.py
python python/demo2_ensemble.py
python python/demo3_spike_hypergraph.py
python python/demo4_causal.py
python python/demo5_dashboard.py
```

Each script also accepts an optional config path:

```bash
python python/demo3_spike_hypergraph.py .tmp_smoke/demo3.yaml
```

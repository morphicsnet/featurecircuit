# featurecircuit Demo Face
> Reproducibility corridor for running the protocol chain end to end and seeing the artifacts land in `demo/runs/`.

## 60-second corridor
```bash
cd demo
python python/demo1_baseline.py
python python/demo2_ensemble.py
python python/demo3_spike_hypergraph.py
```

You should see stamped run directories under `demo/runs/` containing plots, metrics, manifests, and protocol-native artifacts.

## What this face is for
- proving that the protocol chain is runnable, not just well specified
- giving researchers a corridor from baseline features to hypergraphs and causal artifacts
- producing example outputs that downstream tools can validate and diff

## Layout
- `python/`: executable demo scripts and helpers
- `configs/`: run configs and smoke configs
- `notebooks/`: notebook corridor
- `docs/`: architecture, metrics, reproducibility, and checklists
- `examples/outputs/`: reference artifacts

## Choose your path
- I want to run the corridor: [60-second corridor](#60-second-corridor)
- I want the docs map: [demo docs index](docs/README.md)
- I want protocol internals: [core README](../core/README.md)

## Go next
- Root guide: [featurecircuit](../README.md)
- Docs map: [demo/docs README](docs/README.md)
- Historical mirror: [legacy superposition demo](../legacy/superposition-demo/README.md)

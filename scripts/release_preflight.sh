#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/release_preflight.sh [--with-smoke] [--build-artifacts]

Options:
  --with-smoke       Run reduced end-to-end demo smoke corridor.
  --build-artifacts  Build release artifacts under dist/.
EOF
}

WITH_SMOKE=0
BUILD_ARTIFACTS=0

for arg in "$@"; do
  case "$arg" in
    --with-smoke) WITH_SMOKE=1 ;;
    --build-artifacts) BUILD_ARTIFACTS=1 ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "Unknown argument: $arg" >&2
      usage >&2
      exit 2
      ;;
  esac
done

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -d ".venv" ]]; then
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --upgrade pip
pip install maturin pytest jsonschema pyyaml numpy

if [[ "$WITH_SMOKE" -eq 1 ]]; then
  pip install torch transformers scikit-learn matplotlib tqdm
fi

maturin develop --release -m core/py_nsi/Cargo.toml

cargo test --workspace
PYTHONPATH="core/protocol/python:demo" pytest -q tests

# Tooling smoke checks for schema validation and artifact diff.
tmp_fs_json=".tmp/release_preflight_feature_space.v1.json"
mkdir -p .tmp
cat > "${tmp_fs_json}" <<'JSON'
{
  "schema_name": "feature_space.v1",
  "schema_version": 1,
  "feature_space_id": "fs:preflight",
  "feature_space_type": "sae",
  "producer": "release_preflight",
  "producer_version": "v1",
  "model_id": "tiny",
  "layer_map": {"0": "sae"},
  "dim": 2,
  "activation_rule": "topk",
  "checksum": "preflight"
}
JSON
python tools/schema_validate/main.py --path "${tmp_fs_json}" --schema feature_space.v1.json
python tools/artifact_diff/main.py --left "${tmp_fs_json}" --right "${tmp_fs_json}"

tmp_ab_json=".tmp/release_preflight_activation_batch.v1.json"
cat > "${tmp_ab_json}" <<'JSON'
{
  "schema_name": "activation_batch.v1",
  "schema_version": 1,
  "activation_batch_id": "ab:preflight",
  "run_id": "preflight",
  "training_run_id": "preflight",
  "checkpoint_id": "checkpoint-0",
  "batch_id": "batch-0",
  "model_id": "tiny",
  "model_revision": "unknown",
  "tokenizer_id": "tiny",
  "layer_targets": [0],
  "activation_kind": "residual",
  "shape_summary": {"batch": 1, "hidden": 2},
  "dtype": "float32",
  "device": "cpu",
  "metadata": {"runner": "release_preflight"}
}
JSON
python tools/schema_validate/main.py --path "${tmp_ab_json}" --schema activation_batch.v1.json

tmp_snap_json=".tmp/release_preflight_circuit_snapshot.v1.json"
cat > "${tmp_snap_json}" <<'JSON'
{
  "schema_name": "circuit_snapshot.v1",
  "schema_version": 1,
  "snapshot_id": "snap:preflight",
  "run_id": "preflight",
  "training_run_id": "preflight",
  "checkpoint_id": "checkpoint-0",
  "feature_space_id": "fs:preflight",
  "relation_artifact_id": "rel:preflight",
  "structure_artifact_id": "struct:preflight",
  "candidate_set_id": "cand:preflight",
  "candidate_ids": ["c:1"],
  "summary": {"runner": "release_preflight"},
  "metadata": {"runner": "release_preflight"}
}
JSON
python tools/schema_validate/main.py --path "${tmp_snap_json}" --schema circuit_snapshot.v1.json

if [[ "$WITH_SMOKE" -eq 1 ]]; then
  pushd demo >/dev/null
  mkdir -p .tmp_release_smoke
  python - <<'PY'
from __future__ import annotations

from pathlib import Path

import yaml

base = Path("configs")
out = Path(".tmp_release_smoke")
out.mkdir(parents=True, exist_ok=True)

cfg = yaml.safe_load((base / "demo1_baseline.yaml").read_text())
cfg["dataset"]["n_per_class"] = 5
cfg["sae"]["hidden_dim"] = 64
cfg["sae"]["top_k"] = 4
cfg["sae"]["epochs"] = 1
cfg["metrics"]["hist_bins"] = 10
cfg["outputs"]["base_dir"] = "runs/baseline_release_smoke"
cfg["outputs"]["run_tag"] = "smoke"
(out / "demo1.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False))

cfg = yaml.safe_load((base / "demo2_ensemble.yaml").read_text())
cfg["dataset"]["n_per_class"] = 5
cfg["sae_single"]["hidden_dim"] = 64
cfg["sae_single"]["top_k"] = 4
cfg["sae_single"]["epochs"] = 1
cfg["ensemble"]["feature_dim"] = 64
cfg["ensemble"]["top_k"] = 4
cfg["metrics"]["hist_bins"] = 10
cfg["outputs"]["base_dir"] = "runs/ensemble_release_smoke"
cfg["outputs"]["run_tag"] = "smoke"
(out / "demo2.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False))

cfg = yaml.safe_load((base / "demo3_spike_hypergraph.yaml").read_text())
cfg["dataset"]["n_per_class"] = 8
cfg["ensemble"]["feature_dim"] = 64
cfg["ensemble"]["top_k"] = 4
cfg["spike"]["gse_window"] = 0.2
cfg["metrics"]["hist_bins"] = 10
cfg["outputs"]["base_dir"] = "runs/spike_hypergraph_release_smoke"
cfg["outputs"]["run_tag"] = "smoke"
(out / "demo3.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False))

cfg = yaml.safe_load((base / "demo4_causal.yaml").read_text())
cfg["dataset"]["n_samples"] = 24
cfg["ensemble"]["feature_dim"] = 64
cfg["ensemble"]["top_k"] = 4
cfg["spike"]["gse_window"] = 0.2
cfg["acdc"]["max_edges"] = 12
cfg["outputs"]["base_dir"] = "runs/causal_release_smoke"
cfg["outputs"]["run_tag"] = "smoke"
(out / "demo4.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False))

cfg = yaml.safe_load((base / "demo5_dashboard.yaml").read_text())
cfg["runs"]["baseline_dir"] = "runs/baseline_release_smoke"
cfg["runs"]["ensemble_dir"] = "runs/ensemble_release_smoke"
cfg["runs"]["spike_hypergraph_dir"] = "runs/spike_hypergraph_release_smoke"
cfg["runs"]["causal_dir"] = "runs/causal_release_smoke"
(out / "demo5.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False))
PY

  python python/demo1_baseline.py .tmp_release_smoke/demo1.yaml
  python python/demo2_ensemble.py .tmp_release_smoke/demo2.yaml
  python python/demo3_spike_hypergraph.py .tmp_release_smoke/demo3.yaml
  python python/demo4_causal.py .tmp_release_smoke/demo4.yaml
  python python/demo5_dashboard.py .tmp_release_smoke/demo5.yaml
  popd >/dev/null
fi

if [[ "$BUILD_ARTIFACTS" -eq 1 ]]; then
  mkdir -p dist
  maturin build --release -m core/py_nsi/Cargo.toml -o dist
  maturin sdist -m core/py_nsi/Cargo.toml -o dist
  (
    cd dist
    shasum -a 256 py_nsi-* > SHA256SUMS.txt
  )
  scripts/release_verify_artifacts.sh
fi

echo "release preflight complete"

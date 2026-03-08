#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/release_verify_artifacts.sh [wheel-path]

If wheel-path is omitted, the newest py_nsi wheel in dist/ is used.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -n "${1:-}" ]]; then
  WHEEL_PATH="$1"
else
  WHEEL_PATH="$(ls -1t dist/py_nsi-*.whl 2>/dev/null | head -n 1 || true)"
fi

if [[ -z "$WHEEL_PATH" || ! -f "$WHEEL_PATH" ]]; then
  echo "wheel not found. Build one first, e.g. scripts/release_preflight.sh --build-artifacts" >&2
  exit 2
fi

wheel_base="$(basename "$WHEEL_PATH")"
py_tag="$(echo "$wheel_base" | sed -n 's/.*-\(cp[0-9][0-9][0-9]\)-.*/\1/p')"
if [[ -z "$py_tag" ]]; then
  echo "could not infer python tag from wheel name: $wheel_base" >&2
  exit 2
fi
py_mm="${py_tag#cp}"
py_major="${py_mm:0:1}"
py_minor="${py_mm:1:2}"
target_py="${py_major}.${py_minor}"

pick_python() {
  local interp
  for interp in "./.venv/bin/python" python "python${target_py}" "python${py_major}.${py_minor}" "python${py_major}"; do
    if [[ "$interp" == ./* ]]; then
      [[ -x "$interp" ]] || continue
    elif ! command -v "$interp" >/dev/null 2>&1; then
      continue
    fi
    ver="$("$interp" - <<'PY'
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor}")
PY
)"
    if [[ "$ver" == "$target_py" ]]; then
      echo "$interp"
      return 0
    fi
  done
  return 1
}

if ! PYTHON_BIN="$(pick_python)"; then
  echo "no compatible interpreter found for wheel tag ${py_tag}. expected Python ${target_py}." >&2
  exit 2
fi

TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/py_nsi_verify.XXXXXX")"
trap 'rm -rf "$TMP_ROOT"' EXIT

"$PYTHON_BIN" -m venv "$TMP_ROOT/venv"
# shellcheck disable=SC1091
source "$TMP_ROOT/venv/bin/activate"

python -m pip install --upgrade pip
pip install "$WHEEL_PATH"

python - <<'PY'
import py_nsi

required = {
    "SpikeEvent",
    "SpikeEncoder",
    "Island",
    "GraphStreamingEngine",
    "HypergraphStore",
    "EnsembleEncoder",
}
exported = set(getattr(py_nsi, "__all__", []))
missing = sorted(required - exported)
if missing:
    raise SystemExit(f"missing exports from py_nsi.__all__: {missing}")

# Minimal smoke instantiation
enc = py_nsi.SpikeEncoder.from_defaults()
events = enc.encode_batch([[0.0, 1.0]], encoder_id=0)
if not isinstance(events, list):
    raise SystemExit("SpikeEncoder.encode_batch did not return list")
print("artifact install + import smoke OK")
PY

echo "verified wheel: $WHEEL_PATH"

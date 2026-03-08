#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/release_blockers.sh [--version x.y.z]

Checks local release blockers and exits non-zero if any blocker exists.
EOF
}

VERSION="0.1.0"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --version)
      VERSION="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

blockers=()

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  blockers+=("not a git worktree")
else
  if [[ -n "$(git status --porcelain)" ]]; then
    blockers+=("git working tree is not clean")
  fi

  origin_url="$(git remote get-url origin 2>/dev/null || true)"
  if [[ -z "$origin_url" ]]; then
    blockers+=("git remote 'origin' is not configured")
  elif [[ "$origin_url" != http* && "$origin_url" != git@* ]]; then
    blockers+=("git remote 'origin' is local/non-publishable: ${origin_url}")
  fi
fi

if ! grep -q "^## ${VERSION} " CHANGELOG.md 2>/dev/null; then
  blockers+=("CHANGELOG.md missing section header for version ${VERSION} (expected: '## ${VERSION} - ...')")
fi

for artifact in "dist/py_nsi-${VERSION}.tar.gz"; do
  if [[ ! -f "$artifact" ]]; then
    blockers+=("missing artifact: ${artifact}")
  fi
done

if ! ls dist/py_nsi-"${VERSION}"-*.whl >/dev/null 2>&1; then
  blockers+=("missing wheel artifact for ${VERSION} under dist/")
fi

if [[ ! -f "dist/SHA256SUMS.txt" ]]; then
  blockers+=("missing dist/SHA256SUMS.txt")
fi

if (( ${#blockers[@]} > 0 )); then
  echo "release blockers detected:"
  for b in "${blockers[@]}"; do
    echo "  - ${b}"
  done
  if printf '%s\n' "${blockers[@]}" | grep -q "origin"; then
    echo "fix: configure publish remote, e.g. git remote add origin <git-url>"
  fi
  exit 1
fi

echo "no release blockers detected for version ${VERSION}"

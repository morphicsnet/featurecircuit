#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/release_set_origin.sh <git-url>

Configures git remote 'origin' for this repository.
If origin exists, it is updated.
EOF
}

if [[ $# -ne 1 ]]; then
  usage >&2
  exit 2
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

URL="$1"
if [[ "$URL" != http* && "$URL" != git@* ]]; then
  echo "remote URL must be ssh or https git URL: $URL" >&2
  exit 2
fi

if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$URL"
  echo "updated origin -> $URL"
else
  git remote add origin "$URL"
  echo "added origin -> $URL"
fi

git remote -v | sed -n '/^origin\\s/p'

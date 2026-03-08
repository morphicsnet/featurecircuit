#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/release_tag.sh [--version x.y.z] [--push]

Creates an annotated git tag for a release after checking blockers.
EOF
}

VERSION="0.1.0"
PUSH=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --version)
      VERSION="${2:-}"
      shift 2
      ;;
    --push)
      PUSH=1
      shift
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

if [[ "$PUSH" -eq 1 ]]; then
  scripts/release_blockers.sh --version "$VERSION"
else
  scripts/release_blockers.sh --version "$VERSION" --allow-missing-origin
fi

TAG="v${VERSION}"
if git rev-parse "${TAG}" >/dev/null 2>&1; then
  echo "tag already exists: ${TAG}" >&2
  exit 1
fi

git tag -a "${TAG}" -m "Release ${TAG}"
echo "created tag ${TAG}"

if [[ "$PUSH" -eq 1 ]]; then
  git push origin "${TAG}"
  echo "pushed tag ${TAG} to origin"
else
  echo "run 'git push origin ${TAG}' to publish"
fi

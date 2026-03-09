from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _ensure_protocol_path() -> None:
    here = Path(__file__).resolve()
    repo_root = here.parents[2]
    protocol_py = repo_root / "core" / "protocol" / "python"
    if str(protocol_py) not in sys.path:
        sys.path.append(str(protocol_py))


def _infer_schema_name(path: Path) -> str | None:
    name = path.name
    if name.endswith(".jsonl"):
        return name
    if name.endswith(".json"):
        return name
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate protocol artifact JSON/JSONL against schema.")
    parser.add_argument("--path", required=True, help="Artifact path to validate.")
    parser.add_argument("--schema", default=None, help="Schema filename (e.g. feature_space.v1.json).")
    args = parser.parse_args()

    artifact_path = Path(args.path)
    if not artifact_path.exists():
        print(f"error: artifact does not exist: {artifact_path}", file=sys.stderr)
        return 2

    schema_name = args.schema or _infer_schema_name(artifact_path)
    if not schema_name:
        print("error: unable to infer schema name; pass --schema", file=sys.stderr)
        return 2

    _ensure_protocol_path()
    from featurecircuit_protocol.validation import validate_json_file, validate_jsonl_file

    try:
        if schema_name.endswith(".jsonl"):
            validate_jsonl_file(artifact_path, schema_name)
        else:
            validate_json_file(artifact_path, schema_name)
    except Exception as exc:
        print(f"invalid: {artifact_path} against {schema_name}: {exc}", file=sys.stderr)
        return 1

    print(f"valid: {artifact_path} against {schema_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    return json.loads(text)


def _diff_obj(left: Any, right: Any) -> dict[str, Any]:
    if left == right:
        return {"equal": True, "changes": []}

    changes: list[dict[str, Any]] = []
    if isinstance(left, dict) and isinstance(right, dict):
        keys = sorted(set(left.keys()) | set(right.keys()))
        for key in keys:
            if key not in left:
                changes.append({"path": key, "kind": "added"})
            elif key not in right:
                changes.append({"path": key, "kind": "removed"})
            elif left[key] != right[key]:
                changes.append({"path": key, "kind": "changed"})
    elif isinstance(left, list) and isinstance(right, list):
        min_len = min(len(left), len(right))
        for idx in range(min_len):
            if left[idx] != right[idx]:
                changes.append({"path": f"[{idx}]", "kind": "changed"})
        if len(left) > len(right):
            for idx in range(len(right), len(left)):
                changes.append({"path": f"[{idx}]", "kind": "removed"})
        elif len(right) > len(left):
            for idx in range(len(left), len(right)):
                changes.append({"path": f"[{idx}]", "kind": "added"})
    else:
        changes.append({"path": "$", "kind": "type_or_value_changed"})

    return {"equal": False, "changes": changes}


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute a schema-friendly diff between two artifact files.")
    parser.add_argument("--left", required=True, help="Left artifact path.")
    parser.add_argument("--right", required=True, help="Right artifact path.")
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output mode.",
    )
    args = parser.parse_args()

    left_path = Path(args.left)
    right_path = Path(args.right)
    if not left_path.exists() or not right_path.exists():
        print("error: both --left and --right artifacts must exist")
        return 2

    left_payload = _load(left_path)
    right_payload = _load(right_path)
    result = _diff_obj(left_payload, right_payload)

    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["equal"] else 1

    if result["equal"]:
        print("artifacts are equal")
        return 0

    print("artifacts differ:")
    for row in result["changes"]:
        print(f"- {row['kind']}: {row['path']}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

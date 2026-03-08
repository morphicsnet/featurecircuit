from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


_SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas"


def _schema_path(schema_name: str) -> Path:
    p = _SCHEMA_DIR / schema_name
    if not p.exists():
        raise FileNotFoundError(f"schema not found: {p}")
    return p


def load_schema(schema_name: str) -> dict[str, Any]:
    return json.loads(_schema_path(schema_name).read_text(encoding="utf-8"))


def validate_payload(payload: dict[str, Any], schema_name: str) -> None:
    schema = load_schema(schema_name)
    Draft202012Validator(schema).validate(payload)


def validate_json_file(path: str | Path, schema_name: str) -> None:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_payload(payload, schema_name)


def validate_jsonl_file(path: str | Path, schema_name: str) -> None:
    schema = load_schema(schema_name)
    validator = Draft202012Validator(schema)
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        validator.validate(json.loads(line))

from __future__ import annotations

import tomllib
from pathlib import Path


def _load_toml(path: Path) -> dict:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def test_core_and_binding_versions_are_aligned() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    nsi_core_toml = _load_toml(repo_root / "core" / "nsi_core" / "Cargo.toml")
    py_nsi_toml = _load_toml(repo_root / "core" / "py_nsi" / "Cargo.toml")
    pyproject_toml = _load_toml(repo_root / "core" / "py_nsi" / "pyproject.toml")

    nsi_core_version = nsi_core_toml["package"]["version"]
    py_nsi_version = py_nsi_toml["package"]["version"]
    pyproject_version = pyproject_toml["project"]["version"]

    assert nsi_core_version == py_nsi_version == pyproject_version

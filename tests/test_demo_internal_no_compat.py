from __future__ import annotations

from pathlib import Path


def test_demo_internal_code_does_not_import_compat() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    demo_py = repo_root / "demo" / "python"
    offenders: list[str] = []
    for path in demo_py.rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "py_nsi.compat" in text:
            offenders.append(str(path))
    assert not offenders, "demo internal imports must use canonical py_nsi surface: " + ", ".join(offenders)

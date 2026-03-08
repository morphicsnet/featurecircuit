from __future__ import annotations

from pathlib import Path


FORBIDDEN = [
    "core.nsi_core.src",
    "core/nsi_core/src/",
    "core/py_nsi/src/",
    "use crate::core::",
    "legacy/superposition-demo",
    "legacy/superposition-solver1",
]


def test_satellites_do_not_depend_on_core_internal_paths() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sat_root = repo_root / "satellites"
    assert sat_root.exists()

    offenders: list[str] = []
    for path in sat_root.rglob("*"):
        if path.suffix not in {".py", ".rs", ".md", ".toml", ".yaml", ".yml", ".json"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for bad in FORBIDDEN:
            if bad in text:
                offenders.append(f"{path}: contains '{bad}'")

    assert not offenders, "\n".join(offenders)

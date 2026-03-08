from __future__ import annotations

import os
from pathlib import Path


def test_release_support_files_exist() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    expected = [
        repo_root / "LICENSE",
        repo_root / "CHANGELOG.md",
        repo_root / "RELEASE_CHECKLIST.md",
        repo_root / "docs" / "release.md",
        repo_root / "scripts" / "release_preflight.sh",
        repo_root / "scripts" / "release_verify_artifacts.sh",
        repo_root / "scripts" / "release_blockers.sh",
        repo_root / "scripts" / "release_tag.sh",
    ]
    missing = [str(p) for p in expected if not p.exists()]
    assert not missing, "missing release files: " + ", ".join(missing)


def test_release_scripts_are_executable() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    scripts = [
        repo_root / "scripts" / "release_preflight.sh",
        repo_root / "scripts" / "release_verify_artifacts.sh",
        repo_root / "scripts" / "release_blockers.sh",
        repo_root / "scripts" / "release_tag.sh",
    ]
    non_exec = [str(p) for p in scripts if not os.access(p, os.X_OK)]
    assert not non_exec, "release scripts must be executable: " + ", ".join(non_exec)

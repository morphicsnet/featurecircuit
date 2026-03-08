# Release Checklist

## Pre-Release
- [x] Confirm target version (current: `0.1.0`) in:
  - [x] `core/nsi_core/Cargo.toml`
  - [x] `core/py_nsi/Cargo.toml`
  - [x] `core/py_nsi/pyproject.toml`
- [x] Update `CHANGELOG.md` for release contents.
- [x] Run release preflight:
  - [x] `scripts/release_preflight.sh`
- [x] Optional heavy gate:
  - [x] `scripts/release_preflight.sh --with-smoke --build-artifacts`

## Artifact Validation
- [x] Wheel artifacts generated (`dist/*.whl`).
- [x] Source distribution generated (`dist/*.tar.gz`).
- [x] Protocol artifact schema checks pass in tests.

## Release
- [ ] Run blocker gate:
  - [ ] `scripts/release_blockers.sh --version 0.1.0`
- [ ] Ensure publish remote exists:
  - [ ] `scripts/release_set_origin.sh <git-url>`
- [ ] Create and push tag:
  - [ ] `scripts/release_tag.sh --version 0.1.0 --push`
- [ ] Verify `.github/workflows/release.yml` run passes.
- [ ] Attach artifacts/release notes.

## Post-Release
- [x] Install wheel in clean venv and import `py_nsi` (pre-release dry run via `scripts/release_verify_artifacts.sh`).
- [x] Smoke-run at least one demo corridor path.
- [x] Prepare compat cutoff announcement copy (`docs/release_announcement_template.md`).
- [ ] Announce compat cutoff policy (`py_nsi.compat` one release).

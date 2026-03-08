# Release Guide

## Scope
This guide covers release preparation for `featurecircuit-protocol` and `py_nsi` package artifacts.

## Versioning
- First consolidation line uses `0.1.0`.
- Keep versions aligned across:
  - `core/nsi_core/Cargo.toml`
  - `core/py_nsi/Cargo.toml`
  - `core/py_nsi/pyproject.toml`

## Preflight Gate
Run from repository root:

```bash
scripts/release_preflight.sh
```

Optional heavier gate with end-to-end smoke corridor and wheel/sdist build:

```bash
scripts/release_preflight.sh --with-smoke --build-artifacts
```

Artifact install verification (clean temporary venv):

```bash
scripts/release_verify_artifacts.sh
```

Release blocker check (git state, changelog section, origin remote, artifacts):

```bash
scripts/release_blockers.sh --version 0.1.0
```

If `origin` is missing, configure it:

```bash
scripts/release_set_origin.sh <git-url>
```

Outputs:
- Test and build logs in terminal
- Optional built artifacts under `dist/`
- Optional smoke artifacts under `demo/runs/*_release_smoke/smoke`

## Required Pass Criteria
- `cargo test --workspace` passes.
- `pytest -q tests` passes.
- No schema validation errors in protocol artifact writers.
- `demo/python` has no internal `py_nsi.compat` imports.
- Satellite boundary tests pass.

## CI / Release Workflow
- CI: `.github/workflows/ci.yml`
- Tag release build workflow: `.github/workflows/release.yml`
  - Triggered by `v*` tags and `workflow_dispatch`
  - Produces wheel artifacts and source distribution artifact

## Tagging
After preflight passes:

```bash
git tag v0.1.0
git push origin v0.1.0
```

Scripted equivalent:

```bash
scripts/release_tag.sh --version 0.1.0 --push
```

## Post-Tag Validation
- Download wheel artifacts from workflow run.
- Install wheel in a clean venv and verify:

```bash
python -c "import py_nsi; print(py_nsi.__all__)"
```

Equivalent scripted check:

```bash
scripts/release_verify_artifacts.sh dist/<wheel-file>.whl
```

## Compatibility Window
- `py_nsi.compat` is temporary for one consolidation release.
- New internal code must remain on canonical `py_nsi` API.

## Release Comms
- Announcement template: `docs/release_announcement_template.md`

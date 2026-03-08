# Release Announcement Template (`v0.1.0`)

FeatureCircuit Protocol `v0.1.0` is now available.

## Highlights
- Consolidated protocol repo (`superposition-demo` + `superposition-solver1`) into `featurecircuit-protocol`.
- Canonical artifact chain and versioned schemas shipped.
- Deterministic feature/relation/candidate IDs and manifest compatibility checks included.
- Demo corridor aligned to canonical `py_nsi` API.

## Artifacts
- Python wheel(s): `py_nsi-0.1.0-*.whl`
- Source distribution: `py_nsi-0.1.0.tar.gz`

## Compatibility Notice
- `py_nsi.compat` remains available for this consolidation release only.
- It will be removed in the next release line; migrate internal and external usage to canonical `py_nsi` classes now.

## Migration
- Runbook: `docs/migration.md`
- Protocol contracts: `docs/protocol.md`

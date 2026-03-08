# Changelog

## 0.1.0 - Consolidation Release
- Consolidated `superposition-demo` and `superposition-solver1` into `featurecircuit-protocol`.
- Established canonical protocol artifact chain and versioned schemas.
- Added deterministic ID helpers for features, relations, and candidates.
- Added protocol manifest emission and artifact compatibility checks.
- Migrated demo internals to canonical `py_nsi` surface.
- Kept `py_nsi.compat` as temporary compatibility layer (one-release window).
- Added CI tests for schema contracts, deterministic IDs, compatibility behavior, and satellite boundaries.
- Added release preflight script and release workflow scaffolding.

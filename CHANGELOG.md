# Changelog

## 0.1.0 - Consolidation Release
- Consolidated `superposition-demo` and `superposition-solver1` into `featurecircuit-protocol`.
- Established canonical protocol artifact chain and versioned schemas.
- Added deterministic ID helpers for features, relations, and candidates.
- Added protocol manifest emission with lineage/export-profile declarations and artifact compatibility checks.
- Added first-class `activation_batch.v1` and `circuit_snapshot.v1` contracts.
- Added protocol-layer abstract interfaces (`ModelAdapter`, `FeatureAdapter`, `RelationBuilder`, `StructureBuilder`, `ScoreComputer`, `Exporter`) and typed failure classes.
- Added schema validation and artifact-diff CLIs under `tools/`.
- Migrated demo internals to canonical `py_nsi` surface.
- Kept `py_nsi.compat` as temporary compatibility layer (one-release window).
- Added CI tests for schema contracts, deterministic IDs, compatibility behavior, and satellite boundaries.
- Added release preflight script and release workflow scaffolding.

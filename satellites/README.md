# Satellites (Out of Scope)

This directory holds companion modules migrated from earlier repos:
- `nsi-client/`
- `nsi-engine/`

These are treated as satellites for this consolidation release.

## Dependency Rule
Satellites may depend only on:
- public `nsi_core` / `py_nsi` interfaces
- versioned protocol schemas and artifact contracts

Satellites must not depend on internal core implementation paths.

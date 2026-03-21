# featurecircuit Satellites
> Companion modules that live near the protocol stack without being allowed to reach into its private internals.

Satellites are intentionally out of core scope for this release. They can depend on public `nsi_core` / `py_nsi` APIs and versioned protocol artifacts, but not on internal implementation paths.

## What lives here
- [`nsi-client/`](nsi-client/README.md): client-side companion skeleton
- [`nsi-engine/`](nsi-engine/README.md): service/runtime skeleton

## Dependency rule
Satellites may depend only on:
- public `nsi_core` / `py_nsi` interfaces
- versioned protocol schemas and artifact contracts

## Go next
- Root guide: [featurecircuit](../README.md)
- Core boundary: [core README](../core/README.md)
- Historical mirrors: [legacy surfaces](../legacy/superposition-demo/README.md)

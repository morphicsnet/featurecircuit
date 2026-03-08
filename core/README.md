# Core / Protocol Face

`core/` contains the protocol contracts and public runtime primitives.

## Contents
- `nsi_core/`: Rust core crate (kept as stable identifier in first release)
- `py_nsi/`: Python bindings (canonical API) and `py_nsi.compat` shim
- `protocol/`: versioned schemas and reference Python contract helpers

## Public Surface
Consumers should depend on:
- `nsi_core` public crate APIs
- `py_nsi` canonical classes
- schema files under `core/protocol/schemas/`

Consumers should not depend on internal module paths inside core implementation files.

# featurecircuit local checklist

Source of truth: [`/Volumes/128/MAIR/PLAN.md`](/Volumes/128/MAIR/PLAN.md)

## featurecircuit-owned surfaces
- `core/protocol/python/featurecircuit_protocol/mair_bridge.py`
- `tests/test_mair_bridge.py`

## Current blockers
- remove MAIR path hacks from the bridge module
- keep the HIF bridge stable while MAIR and BLT evolve upstream

## Upstream dependency
- `MAIR` and `BLT` must be installed editable before MAIR bridge tests run

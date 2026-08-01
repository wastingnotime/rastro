# Temporal flow validation refinement

## Change

Extended runtime evidence validation to assert that threshold interactions are
chronologically ordered and separated by the configured two-second phase
interval.

## Verification

- `PYTHONPATH=sandboxes/simulation/src:/home/henrique/.wnt/runtime/mrl python3 sandboxes/simulation/tools/validate_runtime_observations.py`
- `git diff --check`

# Threshold history query build

## Change

Added the `ViewWarningThresholdHistory` application query. It returns the
effective warning policy reconstructed from ordered events together with the
append-only event tuple, and the runtime scenario now exercises it.

## Verification

- `PYTHONPATH=sandboxes/simulation/src python3 -m unittest discover -s sandboxes/simulation/tests -q`
- `PYTHONPATH=sandboxes/simulation/src:/home/henrique/.wnt/runtime/mrl python3 sandboxes/simulation/tools/run_maintenance_status.py`
- `git diff --check`

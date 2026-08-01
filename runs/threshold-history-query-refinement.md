# Threshold history query refinement

## Change

Added owner authorization to `ViewWarningThresholdHistory`. Non-owner access
now raises the stable `warning_threshold_history_forbidden` error before any
projection is returned.

## Verification

- `PYTHONPATH=sandboxes/simulation/src python3 -m unittest discover -s sandboxes/simulation/tests -q`
- `PYTHONPATH=sandboxes/simulation/src:/home/henrique/.wnt/runtime/mrl python3 sandboxes/simulation/tools/run_maintenance_status.py`
- `git diff --check`

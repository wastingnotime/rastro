# Threshold use-case runtime refinement

## Change

The MRL runtime scenario now executes `CustomizeWarningThresholds` and
`RestoreManufacturerWarningThresholds`, emits both use-case observations, and
publishes their domain audit events.

## Verification

- `PYTHONPATH=sandboxes/simulation/src python3 -m unittest discover -s sandboxes/simulation/tests -q`
- `PYTHONPATH=sandboxes/simulation/src python3 sandboxes/simulation/tools/run_maintenance_status.py`
- `git diff --check`

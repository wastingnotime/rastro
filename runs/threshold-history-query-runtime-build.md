# Threshold history query runtime build

## Change

Extended the runtime scenario with the forbidden non-owner path for
`ViewWarningThresholdHistory`. The scenario now emits both successful owner
access and a stable rejected application response.

## Verification

- `PYTHONPATH=sandboxes/simulation/src python3 -m unittest discover -s sandboxes/simulation/tests -q`
- `PYTHONPATH=sandboxes/simulation/src:/home/henrique/.wnt/runtime/mrl python3 sandboxes/simulation/tools/run_maintenance_status.py`
- `git diff --check`

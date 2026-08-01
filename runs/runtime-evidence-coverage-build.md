# Runtime evidence coverage build

## Change

Extended the runtime validator beyond threshold history. It now checks owner
status API success/forbidden responses, reminder cadence evidence, and all
three ownership profiles including the long-unused freshness result.

## Verification

- `PYTHONPATH=sandboxes/simulation/src python3 -m unittest discover -s sandboxes/simulation/tests -q`
- `PYTHONPATH=sandboxes/simulation/src:/home/henrique/.wnt/runtime/mrl python3 sandboxes/simulation/tools/validate_runtime_observations.py`
- `git diff --check`

# Runtime observation validator refinement

## Change

Added a repository-owned validator for the maintenance runtime evidence. It
checks the threshold use cases in the catalog, successful command/query
executions, forbidden non-owner access, and the owner-start summary.

## Verification

- `PYTHONPATH=sandboxes/simulation/src python3 -m unittest discover -s sandboxes/simulation/tests -q`
- `PYTHONPATH=sandboxes/simulation/src:/home/henrique/.wnt/runtime/mrl python3 sandboxes/simulation/tools/validate_runtime_observations.py`
- `git diff --check`

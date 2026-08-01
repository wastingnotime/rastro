# Observatory graph refinement

## Change

Limited the shared Observatory's dynamic effect beams to the latest 24 effect
observations. Structural graph edges and complete observation/event history
remain available; only the visual effect layer is bounded for readability.

## Verification

- `PYTHONPATH=sandboxes/simulation/src:/home/henrique/.wnt/runtime/mrl python3 sandboxes/simulation/tools/browser_smoke_test.py`
- `PYTHONPATH=sandboxes/simulation/src:/home/henrique/.wnt/runtime/mrl python3 sandboxes/simulation/tools/validate_runtime_observations.py`
- `git diff --check`

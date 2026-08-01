# Temporal owner-flow build

## Change

Owner-flow observations are now scheduled as two-second simulation phases
after the initial five-second paused start. This gives use-case executions,
domain events, and their rendered beams distinct simulation timestamps while
preserving the existing domain calculations.

## Verification

- `PYTHONPATH=sandboxes/simulation/src python3 -m unittest discover -s sandboxes/simulation/tests -q`
- `PYTHONPATH=sandboxes/simulation/src:/home/henrique/.wnt/runtime/mrl python3 sandboxes/simulation/tools/validate_runtime_observations.py`
- `PYTHONPATH=sandboxes/simulation/src:/home/henrique/.wnt/runtime/mrl python3 sandboxes/simulation/tools/browser_smoke_test.py`
- `git diff --check`

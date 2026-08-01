# Browser smoke-test build

## Change

Added a repository-owned Chromium smoke test for the supervised Observatory.
It verifies the paused initial state, stale-event-free Event source after
reset, the five-second Play delay at 1× pace, event-backed graph updates, and
a visible Observatory canvas. Beam geometry remains a browser-rendered detail
of the graph/event state.

## Verification

- `PYTHONPATH=sandboxes/simulation/src python3 -m unittest discover -s sandboxes/simulation/tests -q`
- `PYTHONPATH=sandboxes/simulation/src:/home/henrique/.wnt/runtime/mrl python3 sandboxes/simulation/tools/browser_smoke_test.py`
- `git diff --check`

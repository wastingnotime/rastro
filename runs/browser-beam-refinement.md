# Browser beam refinement

## Change

Strengthened browser beam verification to require the rendered owner-to-use-case
travelling beam for `CustomizeWarningThresholds`, matching the declared graph
contract. Domain-event nodes are not currently declared graph nodes.

## Verification

- `PYTHONPATH=sandboxes/simulation/src:/home/henrique/.wnt/runtime/mrl python3 sandboxes/simulation/tools/browser_smoke_test.py`
- `git diff --check`

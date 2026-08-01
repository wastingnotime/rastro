# Browser smoke timing refinement

## Change

Adjusted the browser smoke-test event wait to account for the initial paused
start plus the new two-second owner-flow phases.

## Verification

- `PYTHONPATH=sandboxes/simulation/src:/home/henrique/.wnt/runtime/mrl python3 sandboxes/simulation/tools/browser_smoke_test.py`
- `git diff --check`

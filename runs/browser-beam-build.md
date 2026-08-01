# Browser beam verification build

## Change

Added a development-only shared-runtime debug surface exposing active and glow
beam counts. The repository browser smoke test now asserts that a travelling
beam mesh exists after the delayed owner event flow.

## Verification

- `PYTHONPATH=sandboxes/simulation/src:/home/henrique/.wnt/runtime/mrl python3 sandboxes/simulation/tools/browser_smoke_test.py`
- `git diff --check`

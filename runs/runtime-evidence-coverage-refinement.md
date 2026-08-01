# Runtime evidence coverage refinement

## Change

Strengthened runtime evidence assertions to require schema-safe successful API
responses, data-free forbidden responses, and the complete 3-profile by
3-cadence reminder matrix.

## Verification

- `PYTHONPATH=sandboxes/simulation/src python3 -m unittest discover -s sandboxes/simulation/tests -q`
- `PYTHONPATH=sandboxes/simulation/src:/home/henrique/.wnt/runtime/mrl python3 sandboxes/simulation/tools/validate_runtime_observations.py`
- `git diff --check`

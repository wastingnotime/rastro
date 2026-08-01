# Domain-event graph build

## Change

Added declared observatory event nodes and emission edges for threshold
customization/restoration and service recording/voiding. Browser smoke now
requires both the owner-to-use-case beam and the threshold domain-event beam.

## Verification

- `PYTHONPATH=sandboxes/simulation/src python3 -m unittest discover -s sandboxes/simulation/tests -q`
- `PYTHONPATH=sandboxes/simulation/src:/home/henrique/.wnt/runtime/mrl python3 sandboxes/simulation/tools/browser_smoke_test.py`
- `git diff --check`

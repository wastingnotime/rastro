# Maintenance threshold plan build

## Change

Added collection-level threshold history projection. A shared event stream can
now rebuild a complete maintenance plan, while duplicate item titles and
unknown event targets fail explicitly.

## Verification

- `PYTHONPATH=sandboxes/simulation/src python3 -m unittest discover -s sandboxes/simulation/tests -q`
- `git diff --check`

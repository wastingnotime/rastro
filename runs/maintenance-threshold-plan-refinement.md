# Maintenance threshold plan refinement

## Change

Added explicit rejection for unsupported values in threshold history streams.
Single-item and collection-level projections now expose a stable domain error
instead of an incidental attribute error.

## Verification

- `PYTHONPATH=sandboxes/simulation/src python3 -m unittest discover -s sandboxes/simulation/tests -q`
- `git diff --check`

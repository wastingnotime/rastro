# Maintenance threshold event refinement

## Change

Centralized threshold event validation so constructors and history replay use
the same invariant checker. This keeps the replay boundary defensive without
duplicating dimension and value rules.

## Verification

- `PYTHONPATH=sandboxes/simulation/src python3 -m unittest discover -s sandboxes/simulation/tests -q`
- `git diff --check`

# Maintenance threshold use-case refinement

## Change

Aligned the slice contract with the `CustomizeWarningThresholds` command and
added an application-level test confirming that missing threshold input is
rejected through the use-case boundary.

## Verification

- `PYTHONPATH=sandboxes/simulation/src python3 -m unittest discover -s sandboxes/simulation/tests -q`
- `git diff --check`

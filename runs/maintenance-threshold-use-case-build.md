# Maintenance threshold use-case build

## Change

Added the `CustomizeWarningThresholds` application command. It delegates to
the domain transition and returns both the updated maintenance item and its
`WarningThresholdsCustomized` audit event.

## Verification

- `PYTHONPATH=sandboxes/simulation/src python3 -m unittest discover -s sandboxes/simulation/tests -q`
- `git diff --check`

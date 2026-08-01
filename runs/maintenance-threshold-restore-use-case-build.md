# Maintenance threshold restore use-case build

## Change

Added the `RestoreManufacturerWarningThresholds` application command. It
restores canonical values and returns the updated item with its
`WarningThresholdsRestored` audit event.

## Verification

- `PYTHONPATH=sandboxes/simulation/src python3 -m unittest discover -s sandboxes/simulation/tests -q`
- `git diff --check`

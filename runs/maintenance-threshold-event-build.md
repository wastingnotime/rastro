# Maintenance threshold event build

## Change

Added constructor-level validation for threshold customization and restoration
events. Blank titles, negative values, unknown or duplicate dimensions, and
undeclared mileage/date changes are rejected before projection.

## Verification

- `PYTHONPATH=sandboxes/simulation/src python3 -m unittest discover -s sandboxes/simulation/tests -q`
- `git diff --check`

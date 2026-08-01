# Maintenance threshold history refinement

## Change

Strengthened threshold event replay validation. Events now reject duplicate
dimensions and any mileage/date change that is not declared in
`changed_dimensions`.

## Verification

- `PYTHONPATH=sandboxes/simulation/src python3 -m unittest discover -s sandboxes/simulation/tests -q`
- `git diff --check`

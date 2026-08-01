# MRL refinement receipt: maintenance item invariants

Date: 2026-08-01

## Change

Added construction-time validation to `MaintenanceItem` for required titles
and non-negative interval, warning, and persisted manufacturer baseline
values.

## Validation

```text
Ran 76 tests in 0.011s
OK
git diff --check
passed
```

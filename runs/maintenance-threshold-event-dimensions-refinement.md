# MRL refinement receipt: threshold event dimensions

Date: 2026-08-01

## Change

Added `changed_dimensions` to customization and restoration audit events. The
metadata distinguishes mileage-only, date-only, and two-dimensional changes,
and does not report a dimension when its effective value and provenance remain
unchanged.

## Validation

```text
Ran 75 tests in 0.010s
OK
git diff --check
passed
```

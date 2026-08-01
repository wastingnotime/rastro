# MRL refinement receipt: restore manufacturer thresholds

Date: 2026-08-01

## Change

Added `restore_manufacturer_warning_thresholds`, a validated reverse operation
for owner warning overrides. It requires canonical mileage/date values and
resets both provenance dimensions to manufacturer.

## Validation

```text
Ran 74 tests in 0.010s
OK
git diff --check
passed
```

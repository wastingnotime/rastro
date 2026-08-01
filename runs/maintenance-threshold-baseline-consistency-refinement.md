# MRL refinement receipt: baseline consistency

Date: 2026-08-01

## Change

Added construction-time consistency checks requiring manufacturer-sourced
mileage/date warning values to equal their persisted manufacturer baselines.
Owner-sourced values may differ while retaining a restoration baseline.

## Validation

```text
Ran 76 tests in 0.010s
OK
git diff --check
passed
```

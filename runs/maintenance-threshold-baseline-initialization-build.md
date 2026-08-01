# MRL build receipt: initialize manufacturer baselines

Date: 2026-08-01

## Change

`MaintenanceItem` now initializes missing manufacturer warning baselines from
its manufacturer-sourced effective warning values at construction. Imported
owner-sourced policies remain explicit when their canonical baseline is not
known.

## Validation

```text
Ran 76 tests in 0.010s
OK
git diff --check
passed
```

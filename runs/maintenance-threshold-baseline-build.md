# MRL build receipt: persisted manufacturer threshold baseline

Date: 2026-08-01

## Change

Maintenance items now retain `manufacturer_warning_km` and
`manufacturer_warning_days` when an owner override is first applied.
`restore_manufacturer_warning_thresholds` can restore those persisted values
without caller-supplied thresholds, while explicit values remain available for
items imported without a baseline.

## Validation

```text
Ran 75 tests in 0.011s
OK
git diff --check
passed
```

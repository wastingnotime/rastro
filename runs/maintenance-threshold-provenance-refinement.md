# MRL refinement receipt: threshold provenance

Date: 2026-08-01

## Change

Added `ThresholdSource` to maintenance items and
`customize_warning_thresholds` for validated owner warning overrides.
Manufacturer defaults remain explicit, and effective owner thresholds change
status deterministically while retaining their provenance.

## Validation

```text
Ran 72 tests in 0.011s
OK
git diff --check
passed
```

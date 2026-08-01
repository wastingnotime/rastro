# MRL build receipt: threshold customization event

Date: 2026-08-01

## Change

Added the `WarningThresholdsCustomized` domain event and
`customize_warning_thresholds_with_event` operation. Owner warning changes now
retain an auditable before/after threshold record while preserving the existing
item-only customization helper.

## Validation

```text
Ran 73 tests in 0.010s
OK
git diff --check
passed
```

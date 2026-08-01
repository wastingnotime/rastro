# MRL build receipt: assessment threshold provenance

Date: 2026-08-01

## Change

Extended `MaintenanceAssessment` with `warning_source` and propagated the
maintenance item's `ThresholdSource` through every assessment path, including
missing-data and stale-odometer `unknown` results.

## Validation

```text
Ran 72 tests in 0.010s
OK
git diff --check
passed
```

This build changes only domain semantics; adapters remain unchanged.

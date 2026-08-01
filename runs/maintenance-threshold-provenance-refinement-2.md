# MRL refinement receipt: per-dimension threshold provenance

Date: 2026-08-01

## Change

Split warning provenance into `warning_km_source` and
`warning_days_source`. The compatibility `warning_source` accessor returns
`mixed` when those dimensions differ, preventing a partial owner override from
being misrepresented as a full override.

## Validation

```text
Ran 72 tests in 0.010s
OK
git diff --check
passed
```

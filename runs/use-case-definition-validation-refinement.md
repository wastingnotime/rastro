# MRL refinement receipt: use-case definition validation

Date: 2026-08-01

## Change

`UseCaseDefinition` now rejects blank names and purposes at construction time,
preventing invalid entries from entering the typed catalog or runtime
`use_case_catalog` observation.

## Validation

```text
Ran 65 tests in 0.009s
OK

mrl-simulation supervise --scenario-factory \
  app.simulation.mrl_runtime_scenario:create_simulation \
  --port 18774 --once
listening on http://127.0.0.1:18774
```

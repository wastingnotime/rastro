# MRL refinement receipt: typed use-case catalog

Date: 2026-08-01

## Change

Added `UseCaseKind` and the `USE_CASE_KINDS` catalog to the application use-
case package. Runtime observation classification is derived from this single
catalog, and a contract test verifies one query plus four commands.

## Validation

```text
Ran 64 tests in 0.010s
OK

mrl-simulation supervise --scenario-factory \
  app.simulation.mrl_runtime_scenario:create_simulation \
  --port 18770 --once
listening on http://127.0.0.1:18770
```

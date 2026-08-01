# MRL refinement receipt: catalog collision validation

Date: 2026-08-01

## Change

Added `index_use_case_catalog`, which rejects duplicate use-case names and
duplicate stable IDs before deriving runtime lookup maps.

## Validation

```text
Ran 66 tests in 0.010s
OK

mrl-simulation supervise --scenario-factory \
  app.simulation.mrl_runtime_scenario:create_simulation \
  --port 18776 --once
listening on http://127.0.0.1:18776
```

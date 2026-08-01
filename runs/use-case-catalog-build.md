# MRL build receipt: visible use-case catalog

Date: 2026-08-01

## Change

The runtime scenario now emits a `use_case_catalog` observation at startup.
It lists all five application use cases and their query/command kinds before
the execution observations begin.

## Validation

```text
Ran 64 tests in 0.010s
OK

mrl-simulation supervise --scenario-factory \
  app.simulation.mrl_runtime_scenario:create_simulation \
  --port 18771 --once
listening on http://127.0.0.1:18771
```

The semantic log showed one catalog observation followed by five
`use_case_executed` observations.

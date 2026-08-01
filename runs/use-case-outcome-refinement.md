# MRL refinement receipt: use-case outcome shape

Date: 2026-08-01

## Change

Centralized runtime use-case emission in `_emit_use_case`. Every
`use_case_executed` observation now includes a stable `payload.outcome` field
plus operation-specific details.

The observation also includes a stable `kind` field: `ViewOwnerStatus` is a
`query`; the remaining four interactions are `command` use cases.

## Validation

```text
Ran 63 tests in 0.009s
OK

mrl-simulation supervise --scenario-factory \
  app.simulation.mrl_runtime_scenario:create_simulation \
  --port 18768 --once
listening on http://127.0.0.1:18768
```

The semantic log showed five use-case observations with normalized outcomes.

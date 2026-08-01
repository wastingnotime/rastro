# MRL refinement receipt: active service history projection

Date: 2026-08-01

## Change

Added explicit coverage for `ViewServiceHistory` excluding voided records
while retaining their audit events. The runtime now emits the query before and
after a voided record to make that behavior observable.

## Validation

```text
Ran 68 tests in 0.010s
OK

mrl-simulation supervise --scenario-factory \
  app.simulation.mrl_runtime_scenario:create_simulation \
  --port 18778 --once
listening on http://127.0.0.1:18778
```

The post-void observation reported `record_count: 1` and `voided_count: 1`.

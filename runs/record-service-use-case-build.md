# MRL build receipt: record service use case

Date: 2026-08-01

## Change

Added `RecordService` to the application use-case boundary. The runtime now
uses it for the owner service visit and emits its execution as a semantic
observation.

## Validation

```text
Ran 63 tests in 0.010s
OK

mrl-simulation supervise --scenario-factory \
  app.simulation.mrl_runtime_scenario:create_simulation \
  --port 18767 --once
listening on http://127.0.0.1:18767
```

The observation log contains five `use_case_executed` entries, including
`RecordService`.

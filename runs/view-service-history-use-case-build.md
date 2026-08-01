# MRL build receipt: view service history use case

Date: 2026-08-01

## Change

Added the owner-authorized `ViewServiceHistory` query use case. It returns
active append-only service records, excludes voided records, and rejects
non-owner actors. The runtime now executes it after recording a service visit.

## Validation

```text
Ran 67 tests in 0.010s
OK

mrl-simulation supervise --scenario-factory \
  app.simulation.mrl_runtime_scenario:create_simulation \
  --port 18777 --once
listening on http://127.0.0.1:18777
```

The semantic log showed `ViewServiceHistory` with `record_count: 1` and a
successful owner outcome.

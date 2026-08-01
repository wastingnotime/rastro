# MRL build receipt: start paused

Date: 2026-08-01

## Change

The owner startup flow is now scheduled at the initial simulation time instead
of executing during session construction. A supervised session starts paused
with zero domain events and one queued owner-start action.

## Validation

```text
initial_domain_events: 0
initial_scheduled_event: True
after_run_domain_events: 2
Ran 70 tests in 0.010s
OK

mrl-simulation supervise --scenario-factory \
  app.simulation.mrl_runtime_scenario:create_simulation \
  --port 18784 --once
listening on http://127.0.0.1:18784
```

The semantic batch runner continues to drain scheduled actions and emit the
full scenario for offline evidence.

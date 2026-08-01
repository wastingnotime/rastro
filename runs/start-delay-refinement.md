# MRL refinement receipt: delayed owner start

Date: 2026-08-01

## Change

Added a five-second simulated delay before the queued owner startup flow. This
gives the Observatory time to display the initial graph before the use-case
and domain-event sequence begins.

## Validation

```text
next_event: 2026-07-31T00:00:05+00:00
after_run_time: 2026-07-31T00:00:05+00:00
domain_events: 2
Ran 70 tests in 0.009s
OK

mrl-simulation supervise --scenario-factory \
  app.simulation.mrl_runtime_scenario:create_simulation \
  --port 18787 --once
listening on http://127.0.0.1:18787
```

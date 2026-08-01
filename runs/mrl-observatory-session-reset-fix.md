# MRL runtime fix receipt: unique session reset identity

Date: 2026-08-01

## Change

The first reset fix used the scenario `run_id`, but this repository
intentionally keeps that ID stable across resets. The shared runtime now adds
a UUID-backed `session_id` to `SimulationControlState`, and the Observatory
uses it for reset detection.

## Validation

```text
run_id_same: True
session_id_different: True
node --check .../observatory/app.js
passed
Ran 70 tests
OK

mrl-simulation supervise --scenario-factory \
  app.simulation.mrl_runtime_scenario:create_simulation \
  --port 18783 --once
listening on http://127.0.0.1:18783
```

The installed runtime is user-space and not a Git repository; these receipts
are the committed repository record of the external runtime fix.

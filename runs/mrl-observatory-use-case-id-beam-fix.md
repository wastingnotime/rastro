# MRL runtime fix receipt: use-case ID beam target

Date: 2026-08-01

## Problem

The graph node used the stable ID `record-service`, while the execution
observation name was the display name `RecordService`. The Observatory looked
up the display name, fell back to the hidden observation log, and rendered no
visible beam.

## Fix

Updated the installed shared runtime at:

```text
/home/henrique/.wnt/runtime/mrl/mrl_simulation_runtime/observatory/app.js
```

Use-case execution target resolution now prefers
`payload.use_case_id`, with display-name fallback for compatibility.

## Validation

```text
record-service-id-in-graph: True
node --check .../observatory/app.js
passed
Ran 70 tests in 0.010s
OK

mrl-simulation supervise --scenario-factory \
  app.simulation.mrl_runtime_scenario:create_simulation \
  --port 18788 --once
listening on http://127.0.0.1:18788
```

The shared runtime is user-space and not a Git repository; this receipt is the
committed repository record of the external runtime fix.

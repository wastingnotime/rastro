# MRL runtime fix receipt: use-case execution beams

Date: 2026-08-01

## Problem

The Observatory graph contained the `owner`→`record-service` structural edge,
but no travelling beam appeared for `RecordService` execution. The renderer did
not infer targets for `use_case_executed` observations and preferred the
`application-use-case` source label over the owner actor node.

## Fix

Updated the installed shared runtime at:

```text
/home/henrique/.wnt/runtime/mrl/mrl_simulation_runtime/observatory/app.js
```

Use-case execution names now resolve to declared use-case nodes, and owner
account actors such as `owner-1` resolve to the `owner` graph node.

## Validation

```text
record-service-node: True
owner-record-service-edge: True
node --check .../observatory/app.js
passed
Ran 70 tests
OK

mrl-simulation supervise --scenario-factory \
  app.simulation.mrl_runtime_scenario:create_simulation \
  --port 18785 --once
listening on http://127.0.0.1:18785
```

The shared runtime is user-space and not a Git repository; this receipt is the
committed repository record of the external runtime fix.

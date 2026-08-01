# MRL runtime fix receipt: use-case beam timing

Date: 2026-08-01

## Problem

Use-case execution beams were chained behind every earlier observation effect.
With a long deterministic startup trace, the `owner`→`RecordService` beam was
delayed too long to be visible.

## Fix

Updated the installed shared runtime at:

```text
/home/henrique/.wnt/runtime/mrl/mrl_simulation_runtime/observatory/app.js
```

`use_case_executed` beams now start independently. Other effect beams retain
their existing sequential handoff behavior.

## Validation

```text
node --check .../observatory/app.js
passed
Ran 70 tests in 0.012s
OK

mrl-simulation supervise --scenario-factory \
  app.simulation.mrl_runtime_scenario:create_simulation \
  --port 18786 --once
listening on http://127.0.0.1:18786
```

The shared runtime is user-space and not a Git repository; this receipt is the
committed repository record of the external runtime fix.

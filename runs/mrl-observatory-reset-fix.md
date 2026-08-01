# MRL runtime fix receipt: reset event source on new run

Date: 2026-08-01

## Problem

The Observatory Event source panel retained events such as `service_recorded`
and `service_record_voided` after a scenario reset when the new session reused
the same observation positions.

## Fix

Updated the installed shared runtime at:

```text
/home/henrique/.wnt/runtime/mrl/mrl_simulation_runtime/observatory/app.js
```

The Observatory now tracks a runtime-generated `state.session_id` and clears
its observation/event selection whenever the supervised session changes. The
scenario's stable `run_id` remains available for semantic replay, while
observation-position rollback remains as a fallback for compatibility.

The runtime is user-space installed and is not a Git repository, so this
runtime fix cannot receive a repository commit. This receipt is the committed
repository record of the change.

## Validation

```text
node --check /home/henrique/.wnt/runtime/mrl/mrl_simulation_runtime/observatory/app.js
passed

two sessions: same run_id, different session_id

mrl-simulation supervise --scenario-factory \
  app.simulation.mrl_runtime_scenario:create_simulation \
  --port 18782 --once
listening on http://127.0.0.1:18782
```

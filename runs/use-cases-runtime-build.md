# MRL build receipt: runtime use-case integration

Date: 2026-08-01

## Change

The repository-owned runtime scenario now invokes the explicit application use
cases for owner status, preference synchronization, service-record correction,
and odometer recording/correction.

## Validation

```text
PYTHONPATH=sandboxes/simulation/src python3 -m unittest discover -s sandboxes/simulation/tests -v
Ran 62 tests in 0.010s
OK

git diff --check
passed
```

The supervised runtime was executed successfully through the MRL launcher:

```text
PYTHONPATH=sandboxes/simulation/src mrl-simulation supervise \
  --scenario-factory app.simulation.mrl_runtime_scenario:create_simulation \
  --port 18766 --once
listening on http://127.0.0.1:18766
```

The default port was already occupied, so the validation used an alternate
local port.

The semantic observation runner also exposed the four application use cases:

```text
SyncAttentionPreferences       preference_sync_accepted
ViewOwnerStatus                attention_count=2
CorrectServiceRecord           service_correction_forbidden
RecordOdometerReading          reading_count=2
```

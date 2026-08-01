# MRL refinement receipt: use-case observability

Date: 2026-08-01

## Change

The runtime adapter now emits a `use_case_executed` observation whenever a
named application use case runs. The observation includes the use-case name,
actor, and outcome payload. This build adds `RecordService` to the explicit
application boundary.

## Validation

```text
PYTHONPATH=sandboxes/simulation/src:/home/henrique/.wnt/runtime/mrl \
python3 sandboxes/simulation/tools/run_maintenance_status.py \
| rg 'use_case_executed'

5 observations returned:
SyncAttentionPreferences
ViewOwnerStatus
RecordService
CorrectServiceRecord
RecordOdometerReading
```

The unit suite remains green: 62 tests passed.

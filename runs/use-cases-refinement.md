# MRL refinement receipt: explicit use cases

Date: 2026-08-01

## Change

Added an explicit `application/use_cases/` boundary for the simulation:

- `ViewOwnerStatus`
- `CorrectServiceRecord`
- `SyncAttentionPreferences`
- `RecordOdometerReading`

The existing domain functions and framework-neutral response helpers remain
available beneath that boundary. The owner status API now invokes the named
status query use case.

## Validation

```text
PYTHONPATH=sandboxes/simulation/src python3 -m unittest discover -s sandboxes/simulation/tests -v
Ran 62 tests in 0.011s
OK
```

`git diff --check` passed.

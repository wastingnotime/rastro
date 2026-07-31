# Validation receipt: maintenance-status-first-slice

Date: 2026-07-31

Commands:

```text
PYTHONPATH=sandboxes/simulation/src python3 -m unittest discover -s sandboxes/simulation/tests -v
mrl-simulation supervise --scenario-factory app.simulation.mrl_runtime_scenario:create_simulation --port 18765 --once
```

Result: 7 unit tests passed; the runtime scenario started and completed.

Observed behavior:

- Engine oil: `ok`, 1,580 km remaining.
- Chain inspection: `approaching_due`, 480 km remaining.
- Next action: `Chain inspection`.
- Invariant `unknown_data_is_not_healthy`: passed.

Note: port `18765` was used because other supervised local sessions already
occupied the runtime default port.

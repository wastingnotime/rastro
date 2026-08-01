# Motorcycle maintenance simulation

This is the repository-owned MRL simulation surface for exploring motorcycle
ownership behavior over time. It is not production application code.

## First slice

The first slice models maintenance status for mileage-driven, time-driven, and
combined maintenance items. It answers whether an item is `ok`,
`approaching_due`, `due`, `overdue`, or `unknown`, and emits the owner's next
action from a deterministic scenario.

Run the tests with:

```bash
PYTHONPATH=sandboxes/simulation/src python3 -m unittest discover -s sandboxes/simulation/tests -v
```

Run the supervised runtime scenario with:

```bash
mrl-simulation supervise --scenario-factory app.simulation.mrl_runtime_scenario:create_simulation --once
```

Validate the required semantic observations for threshold history, owner
status/API access, reminder cadence, and ownership profiles with:

```bash
PYTHONPATH=sandboxes/simulation/src:/home/henrique/.wnt/runtime/mrl \
  python3 sandboxes/simulation/tools/validate_runtime_observations.py
```

The validator also confirms that forbidden API responses do not expose
attention data and that every ownership profile is evaluated at 7, 14, and 30
day reminder cadences.

Run the browser smoke test with Chromium and Playwright. It checks the paused
reset state, then uses Play at 1× pace to verify the delayed owner flow:

```bash
PYTHONPATH=sandboxes/simulation/src:/home/henrique/.wnt/runtime/mrl \
  python3 sandboxes/simulation/tools/browser_smoke_test.py
```

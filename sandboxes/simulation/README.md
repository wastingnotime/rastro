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

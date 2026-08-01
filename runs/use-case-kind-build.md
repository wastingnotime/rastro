# MRL build receipt: use-case kind classification

Date: 2026-08-01

## Change

The `use_case_executed` observation contract now includes a stable `kind`
field. The owner status interaction is classified as a query; service,
correction, preference, and odometer interactions are commands.

## Validation

```text
Ran 63 tests in 0.010s
OK

mrl-simulation supervise --scenario-factory \
  app.simulation.mrl_runtime_scenario:create_simulation \
  --port 18769 --once
listening on http://127.0.0.1:18769
```

The semantic observation log showed one `query` and four `command` use cases.

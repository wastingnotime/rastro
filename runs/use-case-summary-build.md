# MRL build receipt: use-case execution summaries

Date: 2026-08-01

## Change

The runtime now emits `use_case_summary` observations after each execution
phase. Summaries include execution count, query/command counts, outcome counts,
and the names executed in that phase.

## Validation

```text
Ran 64 tests in 0.011s
OK

mrl-simulation supervise --scenario-factory \
  app.simulation.mrl_runtime_scenario:create_simulation \
  --port 18773 --once
listening on http://127.0.0.1:18773
```

The semantic log showed an `owner-start` summary for four interactions and an
`odometer-invariant` summary for the fifth interaction.

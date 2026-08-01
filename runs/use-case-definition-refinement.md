# MRL refinement receipt: use-case purposes

Date: 2026-08-01

## Change

Replaced the name/kind-only catalog entries with typed `UseCaseDefinition`
records. Each definition now carries a purpose, and `USE_CASE_KINDS` remains a
derived compatibility lookup.

## Validation

```text
Ran 64 tests in 0.010s
OK

mrl-simulation supervise --scenario-factory \
  app.simulation.mrl_runtime_scenario:create_simulation \
  --port 18772 --once
listening on http://127.0.0.1:18772
```

The semantic catalog observation includes five names, five kinds, and five
non-empty purposes.

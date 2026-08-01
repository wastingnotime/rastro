# MRL build receipt: stable use-case IDs

Date: 2026-08-01

## Change

Added stable IDs to `UseCaseDefinition` records and derived `USE_CASE_IDS`
lookup. Catalog, execution, and phase-summary observations now include the
same machine-readable `use_case_id` values.

## Validation

```text
Ran 65 tests in 0.009s
OK

mrl-simulation supervise --scenario-factory \
  app.simulation.mrl_runtime_scenario:create_simulation \
  --port 18775 --once
listening on http://127.0.0.1:18775
```

The semantic log correlated display names with stable IDs such as
`view-owner-status` and `record-service`.

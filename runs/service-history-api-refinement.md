# MRL refinement receipt: service history API privacy evidence

Date: 2026-08-01

## Change

The runtime scenario now exercises the service-history API as both the owner
and a non-owner. The forbidden response reports 403 and explicitly confirms
that no `records` field is exposed.

## Validation

```text
Ran 70 tests in 0.009s
OK

mrl-simulation supervise --scenario-factory \
  app.simulation.mrl_runtime_scenario:create_simulation \
  --port 18780 --once
listening on http://127.0.0.1:18780
```

Observed responses: owner `200` with one record; mechanic `403` with
`records_exposed: false`.

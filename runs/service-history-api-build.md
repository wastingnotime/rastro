# MRL build receipt: service history API

Date: 2026-08-01

## Change

Added the thin `GET`-style service-history adapter contract at
`/api/v1/motorcycles/{motorcycle_id}/service-history`. It reuses
`ViewServiceHistory`, returns versioned active records for the owner, and
returns a private-by-default 403 envelope for other actors.

## Validation

```text
Ran 70 tests in 0.009s
OK

mrl-simulation supervise --scenario-factory \
  app.simulation.mrl_runtime_scenario:create_simulation \
  --port 18779 --once
listening on http://127.0.0.1:18779
```

The runtime API observation reported status 200, schema version 1, and one
active record.
